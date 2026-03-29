mod commands;
pub mod watcher;

use commands::pipeline::EvidenceWatcherState;
use commands::terminal::TerminalState;
use watcher::WatcherState;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(TerminalState::default())
        .manage(WatcherState::default())
        .manage(EvidenceWatcherState::default())
        .setup(|app| {
            // On macOS, override the default Cmd+W behavior
            // by removing the Close menu item accelerator.
            // The frontend handles Cmd+W as "close tab" instead.
            #[cfg(target_os = "macos")]
            {
                use tauri::menu::{MenuBuilder, SubmenuBuilder};

                let app_menu = SubmenuBuilder::new(app, "Research Agent")
                    .about(None)
                    .separator()
                    .hide()
                    .hide_others()
                    .show_all()
                    .separator()
                    .quit()
                    .build()?;

                let edit_menu = SubmenuBuilder::new(app, "Edit")
                    .undo()
                    .redo()
                    .separator()
                    .cut()
                    .copy()
                    .paste()
                    .select_all()
                    .build()?;

                let window_menu = SubmenuBuilder::new(app, "Window")
                    .minimize()
                    .build()?;

                let menu = MenuBuilder::new(app)
                    .item(&app_menu)
                    .item(&edit_menu)
                    .item(&window_menu)
                    .build()?;

                app.set_menu(menu)?;
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::fs::read_file,
            commands::fs::write_file,
            commands::fs::list_directory,
            commands::fs::list_sources,
            commands::fs::list_claims,
            commands::fs::update_source_status,
            commands::fs::append_human_notes,
            commands::fs::search_sources,
            commands::fs::read_provenance,
            commands::fs::list_figures,
            commands::fs::update_claim,
            commands::state::read_paper_state,
            commands::state::validate_paper_project,
            commands::state::read_paper_config,
            commands::state::get_recent_projects,
            commands::state::add_recent_project,
            commands::latex::compile_latex,
            commands::terminal::spawn_terminal,
            commands::terminal::write_terminal,
            commands::terminal::resize_terminal,
            commands::terminal::kill_terminal,
            commands::pipeline::run_pipeline_action,
            commands::pipeline::stop_evidence_watcher,
            crate::watcher::start_watching,
            crate::watcher::stop_watching,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
