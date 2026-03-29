use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use serde::Serialize;
use std::collections::HashMap;
use std::io::{Read, Write};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager};

pub struct TerminalState {
    terminals: Mutex<HashMap<u32, TerminalInstance>>,
    next_id: Mutex<u32>,
}

struct TerminalInstance {
    writer: Box<dyn Write + Send>,
    _reader_thread: std::thread::JoinHandle<()>,
    master: Box<dyn portable_pty::MasterPty + Send>,
}

impl Default for TerminalState {
    fn default() -> Self {
        Self {
            terminals: Mutex::new(HashMap::new()),
            next_id: Mutex::new(1),
        }
    }
}

#[derive(Serialize, Clone)]
struct TerminalData {
    id: u32,
    data: String,
}

#[derive(Serialize, Clone)]
struct TerminalExit {
    id: u32,
}

#[tauri::command]
pub fn spawn_terminal(app: AppHandle, cwd: String) -> Result<u32, String> {
    let state = app.state::<TerminalState>();
    let id = {
        let mut next = state.next_id.lock().unwrap();
        let id = *next;
        *next += 1;
        id
    };

    let pty_system = native_pty_system();
    let pair = pty_system
        .openpty(PtySize {
            rows: 24,
            cols: 80,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|e| format!("Failed to open PTY: {}", e))?;

    let mut cmd = CommandBuilder::new_default_prog();
    cmd.cwd(&cwd);

    pair.slave
        .spawn_command(cmd)
        .map_err(|e| format!("Failed to spawn shell: {}", e))?;

    let writer = pair
        .master
        .take_writer()
        .map_err(|e| format!("Failed to get PTY writer: {}", e))?;

    let mut reader = pair
        .master
        .try_clone_reader()
        .map_err(|e| format!("Failed to get PTY reader: {}", e))?;

    let app_clone = app.clone();
    let reader_thread = std::thread::spawn(move || {
        let mut buf = [0u8; 4096];
        loop {
            match reader.read(&mut buf) {
                Ok(0) => break,
                Ok(n) => {
                    let data = String::from_utf8_lossy(&buf[..n]).to_string();
                    let _ = app_clone.emit("terminal-data", TerminalData { id, data });
                }
                Err(_) => break,
            }
        }
        let _ = app_clone.emit("terminal-exit", TerminalExit { id });
    });

    state.terminals.lock().unwrap().insert(
        id,
        TerminalInstance {
            writer,
            _reader_thread: reader_thread,
            master: pair.master,
        },
    );

    Ok(id)
}

#[tauri::command]
pub fn write_terminal(app: AppHandle, id: u32, data: String) -> Result<(), String> {
    let state = app.state::<TerminalState>();
    let mut terminals = state.terminals.lock().unwrap();
    if let Some(term) = terminals.get_mut(&id) {
        term.writer
            .write_all(data.as_bytes())
            .map_err(|e| format!("Write failed: {}", e))?;
        term.writer
            .flush()
            .map_err(|e| format!("Flush failed: {}", e))?;
        Ok(())
    } else {
        Err(format!("Terminal {} not found", id))
    }
}

#[tauri::command]
pub fn resize_terminal(app: AppHandle, id: u32, rows: u16, cols: u16) -> Result<(), String> {
    let state = app.state::<TerminalState>();
    let mut terminals = state.terminals.lock().unwrap();
    if let Some(term) = terminals.get_mut(&id) {
        term.master
            .resize(PtySize {
                rows,
                cols,
                pixel_width: 0,
                pixel_height: 0,
            })
            .map_err(|e| format!("Resize failed: {}", e))?;
        Ok(())
    } else {
        Err(format!("Terminal {} not found", id))
    }
}

#[tauri::command]
pub fn kill_terminal(app: AppHandle, id: u32) -> Result<(), String> {
    let state = app.state::<TerminalState>();
    let mut terminals = state.terminals.lock().unwrap();
    // Dropping the terminal instance will close the PTY
    terminals.remove(&id);
    Ok(())
}
