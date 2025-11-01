// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem, SystemTraySubmenu, WindowEvent
};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use log::{info, error, warn};

// Runner state management
#[derive(Clone)]
struct RunnerState {
    python_process: Arc<Mutex<Option<std::process::Child>>>,
    is_running: Arc<Mutex<bool>>,
}

impl RunnerState {
    fn new() -> Self {
        Self {
            python_process: Arc::new(Mutex::new(None)),
            is_running: Arc::new(Mutex::new(false)),
        }
    }
}

// Tauri commands
#[tauri::command]
async fn start_python_runner(state: tauri::State<'_, RunnerState>) -> Result<String, String> {
    info!("Starting Python runner...");
    
    let mut process_guard = state.python_process.lock().unwrap();
    let mut running_guard = state.is_running.lock().unwrap();
    
    // Kill existing process if running
    if let Some(mut child) = process_guard.take() {
        let _ = child.kill();
        let _ = child.wait();
    }
    
    // Start new Python process
    match Command::new("python")
        .arg("main.py")
        .current_dir("src")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => {
            *process_guard = Some(child);
            *running_guard = true;
            info!("Python runner started successfully");
            Ok("Python runner started".to_string())
        }
        Err(e) => {
            error!("Failed to start Python runner: {}", e);
            Err(format!("Failed to start Python runner: {}", e))
        }
    }
}

#[tauri::command]
async fn stop_python_runner(state: tauri::State<'_, RunnerState>) -> Result<String, String> {
    info!("Stopping Python runner...");
    
    let mut process_guard = state.python_process.lock().unwrap();
    let mut running_guard = state.is_running.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        match child.kill() {
            Ok(_) => {
                let _ = child.wait();
                *running_guard = false;
                info!("Python runner stopped successfully");
                Ok("Python runner stopped".to_string())
            }
            Err(e) => {
                error!("Failed to stop Python runner: {}", e);
                Err(format!("Failed to stop Python runner: {}", e))
            }
        }
    } else {
        warn!("No Python runner process to stop");
        Ok("No runner process to stop".to_string())
    }
}

#[tauri::command]
async fn get_runner_status(state: tauri::State<'_, RunnerState>) -> Result<bool, String> {
    let running_guard = state.is_running.lock().unwrap();
    Ok(*running_guard)
}

#[tauri::command]
async fn open_logs_folder() -> Result<String, String> {
    let logs_path = dirs::home_dir()
        .ok_or("Could not find home directory")?
        .join(".oriphim")
        .join("logs");
    
    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(logs_path.to_string_lossy().to_string())
            .spawn()
            .map_err(|e| format!("Failed to open logs folder: {}", e))?;
    }
    
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(logs_path.to_string_lossy().to_string())
            .spawn()
            .map_err(|e| format!("Failed to open logs folder: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(logs_path.to_string_lossy().to_string())
            .spawn()
            .map_err(|e| format!("Failed to open logs folder: {}", e))?;
    }
    
    Ok("Logs folder opened".to_string())
}

fn create_system_tray() -> SystemTray {
    let open = CustomMenuItem::new("open".to_string(), "Open Runner");
    let start = CustomMenuItem::new("start".to_string(), "Start Runner");
    let stop = CustomMenuItem::new("stop".to_string(), "Stop Runner");
    let logs = CustomMenuItem::new("logs".to_string(), "View Logs");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(open)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(start)
        .add_item(stop)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(logs)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
    
    SystemTray::new().with_menu(tray_menu)
}

fn handle_system_tray_event(app: &tauri::AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::LeftClick { .. } => {
            // Show main window on left click
            let window = app.get_window("main").unwrap();
            let _ = window.show();
            let _ = window.set_focus();
        }
        SystemTrayEvent::MenuItemClick { id, .. } => {
            match id.as_str() {
                "open" => {
                    let window = app.get_window("main").unwrap();
                    let _ = window.show();
                    let _ = window.set_focus();
                }
                "start" => {
                    let app_handle = app.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = app_handle.state::<RunnerState>();
                        if let Err(e) = start_python_runner(state).await {
                            error!("Failed to start runner from tray: {}", e);
                        }
                    });
                }
                "stop" => {
                    let app_handle = app.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = app_handle.state::<RunnerState>();
                        if let Err(e) = stop_python_runner(state).await {
                            error!("Failed to stop runner from tray: {}", e);
                        }
                    });
                }
                "logs" => {
                    tauri::async_runtime::spawn(async move {
                        if let Err(e) = open_logs_folder().await {
                            error!("Failed to open logs from tray: {}", e);
                        }
                    });
                }
                "quit" => {
                    // Stop Python runner before quitting
                    let app_handle = app.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = app_handle.state::<RunnerState>();
                        let _ = stop_python_runner(state).await;
                        app_handle.exit(0);
                    });
                }
                _ => {}
            }
        }
        _ => {}
    }
}

fn main() {
    env_logger::init();
    info!("Starting Oriphim Runner...");
    
    let runner_state = RunnerState::new();
    
    tauri::Builder::default()
        .manage(runner_state)
        .system_tray(create_system_tray())
        .on_system_tray_event(handle_system_tray_event)
        .on_window_event(|event| match event.event() {
            WindowEvent::CloseRequested { api, .. } => {
                // Hide window instead of closing on X button
                event.window().hide().unwrap();
                api.prevent_close();
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            start_python_runner,
            stop_python_runner,
            get_runner_status,
            open_logs_folder
        ])
        .setup(|app| {
            // Auto-start Python runner on app startup
            let app_handle = app.handle();
            let runner_state = app_handle.state::<RunnerState>();
            
            tauri::async_runtime::spawn(async move {
                tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                if let Err(e) = start_python_runner(runner_state).await {
                    error!("Failed to auto-start Python runner: {}", e);
                }
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}