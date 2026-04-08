
from email.mime import audio, message, text
from tkinter import filedialog
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import os  
from rag.auth_engine import AuthEngine  

import customtkinter as ctk
import time
import threading
import webbrowser
from datetime import datetime, timedelta
import threading

import cv2

import mss


from audio_engine import AudioSTTEngine
from rag.slide_extractor import SlideExtractor
from refinement_engine import RefinementEngine
import threading
import os
import json
from tkinter import filedialog
import sounddevice as sd
import wave
import numpy as np
from typing import Any, Dict, List, cast
from functools import partial
import re
ctk.set_default_color_theme("dark-blue")
ctk.set_appearance_mode("dark")
from storage_manager import StorageManager
from merge_engine import MergeEngine
from win10toast_click import ToastNotifier
from pkg_resources import Requirement
from typing import Optional
from rag.ask_engine import AskEngine

class MeetingSystemUI(ctk.CTk):

    BG = "#0b0813"         # Pure deep space background
    CARD = "#151226"       # Rich translucent purple/blue glass
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#9b92b3" # Soft lavender-tinted gray
    ACCENT = "#4f46e5"     # Vibrant Neon Indigo
    ACCENT_SOFT = "#6b62ff"
    SUCCESS = "#10b981"    # Mint neon green
    DANGER = "#d94b58"     # Soft premium coral/red
    DISABLED = "#231f36"
    BORDER = "#2f294d"     # Bright enough to look like a glass edge
    RADIUS_CARD = 20
    RADIUS_BTN = 10
    FONT_FAMILY = "Inter"
    
    def __init__(self):
        super().__init__()

        self.is_capturing = False
        self.start_time = None
        self.timer_running = False
        self.auto_start_timer = None
        self._timeline_tags = {}
        self.current_class_title = "Set class"
        self.current_meeting_link = ""
        self.class_start_time = None
        self.class_triggered = False
        self.toast_active = False
        self._audio_stream = None
        self._audio_playing = False
        self._audio_current_elapsed = 0.0
        self._audio_start_time = None
        self._playback_audio = None
        self._playback_rate = None
        self._playback_pos = 0
        self._playback_stream = None
        self._is_playing = False
        self._playback_audio = None
        self._audio_total_frames = 0
        self._audio_duration_sec = 0
        self._is_loading_audio = False
        self._user_scrolled = False
        self._last_ui_update_time = 0
        self._playback_speed = 1.0
        self._search_after_id = None
        self._live_search_delay = 300  # ms
        self._live_search_enabled = True
        self._stream = None
        self._is_playing = False
        self._is_seeking = False
        self._is_changing_speed = False
        self._user_scrolled = False
        self._scroll_reset_after_id = None
        self._last_seek_click = 0.0
        self._active_timeline_tag = None
        self._playback_state = "idle"
        self._pending_seek_pos = None
        self._active_transcript_tag = None
        self._last_playback_pos = 0
        self._bookmarks = []
        self._audio_loaded = False
        self._refinement_running = False
        self._target_window = None
        self.capture_mode = "audio_video"
        self.vision_model = SentenceTransformer('clip-ViT-B-32')
        # ================= AUTHENTICATION LOCK =================
        self.auth = AuthEngine()
        self.current_user = None
        self._build_login_screen()
        
 

        self.ask_engine: Optional[AskEngine] = None




# states: idle | loading | playing | paused | seeking


        

        # ================= SCHEDULING STATE =================
        self.schedule_active = False
        self.class_source = None  # "manual" | "scheduled"

        self.title("meetingSystem")
        self.geometry("1400x900")
        self.resizable(True, True)
        self.configure(fg_color=self.BG)
        self.attributes("-alpha", 0.0)
        self.audio_engine = None
        self.storage = StorageManager()
        self.storage_start_time = time.time()
        # 🔥 NEW: Intercept the Windows 'X' close button to kill background threads
        self.protocol("WM_DELETE_WINDOW", self._hard_exit_app)

        # ================= MASTER LAYOUT (SIDEBAR + MAIN) =================
        # 1. The Fixed Left Sidebar
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#07090f", corner_radius=0, border_color=self.BORDER, border_width=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) # Prevents sidebar from shrinking

        # 2. The Scrollable Main Workspace (Right)
        self.main_container = ctk.CTkScrollableFrame(self, fg_color=self.BG, corner_radius=0)
        self.main_container.pack(side="right", fill="both", expand=True)

        # ================= ROOT WORKSPACE =================
        # ================= ROOT WORKSPACE =================
        self.root = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.root.pack(fill="both", expand=True, padx=40, pady=40)

        # Subtle Background Glow
        # ✨ Cosmic Nebula Background Glows
        bg_glow_1 = ctk.CTkLabel(self.root, text="", fg_color="#1c123b", width=1200, height=1200, corner_radius=600)
        bg_glow_1.place(relx=0.8, rely=0.1, anchor="center")
        bg_glow_1.lower()

        bg_glow_2 = ctk.CTkLabel(self.root, text="", fg_color="#0e1736", width=900, height=900, corner_radius=450)
        bg_glow_2.place(relx=0.1, rely=0.9, anchor="center")
        bg_glow_2.lower()

        # 🔥 THE NEW LAYOUT SPLIT
        self.middle_column = ctk.CTkFrame(self.root, fg_color="transparent")
        self.middle_column.pack(side="left", fill="both", expand=True, padx=(0, 30))

        self.right_column = ctk.CTkFrame(self.root, fg_color="transparent", width=380)
        self.right_column.pack(side="right", fill="y")
        self.right_column.pack_propagate(False) # Locks the width

        # ================= SIDEBAR CONTENT =================
        # Brand Title
        self.brand_label = ctk.CTkLabel(self.sidebar, text="meetFit", font=ctk.CTkFont(family=self.FONT_FAMILY, size=24, weight="bold"), text_color=self.TEXT_PRIMARY)
        self.brand_label.pack(anchor="w", padx=24, pady=(40, 4))
        
        self.brand_sub = ctk.CTkLabel(self.sidebar, text="AI Study OS", font=ctk.CTkFont(family=self.FONT_FAMILY, size=13), text_color=self.TEXT_SECONDARY)
        self.brand_sub.pack(anchor="w", padx=24, pady=(0, 40))

        # Navigation Menu Header
        ctk.CTkLabel(self.sidebar, text="MENU", font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, weight="bold"), text_color=self.DISABLED).pack(anchor="w", padx=24, pady=(0, 10))

        # Reusable Sidebar Button Builder
        # Reusable Sidebar Button Builder
        def create_nav_btn(text, command, is_primary=False):
            btn = ctk.CTkButton(
                self.sidebar, 
                text=text, 
                anchor="w", 
                height=44, 
                corner_radius=10,
                fg_color=self.ACCENT if is_primary else "transparent",
                hover_color="#1a1d25",
                text_color="#ffffff" if is_primary else self.TEXT_SECONDARY,
                font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
                command=command,
                cursor="hand2"
            )
            btn.pack(fill="x", padx=12, pady=4)
            return btn

        
        # Build Sidebar Buttons
        self.dashboard_btn = create_nav_btn("📊  Dashboard", self.open_dashboard_overlay, is_primary=True)
        self.schedule_btn = create_nav_btn("📅  Schedule Class", self.open_schedule_overlay)
        self.global_stats_btn = create_nav_btn("📈  OS Stats", self.open_global_dashboard)
        self.settings_btn = create_nav_btn("⚙️  Settings", self.open_settings_modal) # 🔥 NEW

        # 🔥 NEW: Embedded Mini-Stats Panel
        # 🔥 NEW: Embedded Mini-Stats Panel
        self.mini_stats_frame = ctk.CTkFrame(self.sidebar, fg_color=self.CARD, corner_radius=12, border_color=self.BORDER, border_width=1)
        self.mini_stats_frame.pack(fill="x", padx=16, pady=(15, 0))

        self.lbl_mini_classes = ctk.CTkLabel(self.mini_stats_frame, text="📚 Classes: 0", text_color=self.TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_mini_classes.pack(anchor="w", padx=16, pady=(12, 4))

        self.lbl_mini_words = ctk.CTkLabel(self.mini_stats_frame, text="📝 Words: 0", text_color=self.TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_mini_words.pack(anchor="w", padx=16, pady=4)

        self.lbl_mini_audio = ctk.CTkLabel(self.mini_stats_frame, text="🎙️ Audio: 0h 0m", text_color=self.TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_mini_audio.pack(anchor="w", padx=16, pady=(4, 12))

        # Start the background loop to keep these updated
        self._refresh_mini_stats()

        # Spacer to push Cloud Sync to the bottom
        
        # Spacer to push Cloud Sync to the bottom
        # Spacer to push everything below it to the bottom
        # ================= 1. BOTTOM SIDEBAR CONTAINER =================
        # 🔥 Pack this FIRST with side="bottom" so it permanently claims its space!
        bottom_sidebar_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_sidebar_frame.pack(side="bottom", fill="x", pady=(0, 24))

        # --- Cloud Sync Button ---
        self.cloud_sync_btn = ctk.CTkButton(
            bottom_sidebar_frame, # Packed inside the new bottom container
            text="☁️  Cloud Sync", 
            anchor="w", 
            height=44, 
            corner_radius=10,
            fg_color=self.ACCENT,
            hover_color="#1a1d25",
            text_color="#ffffff",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            command=self.open_cloud_modal,
            cursor="hand2"
        )
        self.cloud_sync_btn.pack(side="top", fill="x", padx=12, pady=(0, 16))

        # --- Profile Frame ---
        # --- Profile Frame ---
        profile_frame = ctk.CTkFrame(bottom_sidebar_frame, fg_color=self.CARD, corner_radius=16, border_width=1, border_color=self.BORDER)
        profile_frame.pack(side="top", fill="x", padx=16)

        self.avatar_lbl = ctk.CTkLabel(profile_frame, text="?", font=ctk.CTkFont(size=13, weight="bold"), width=38, height=38, corner_radius=19, fg_color=self.ACCENT, text_color="#ffffff")
        self.avatar_lbl.pack(side="left", padx=(12, 10), pady=12)

        text_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        self.profile_name_lbl = ctk.CTkLabel(text_frame, text="User", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"), text_color=self.TEXT_PRIMARY)
        self.profile_name_lbl.pack(anchor="w", pady=0)
        
        # 🔥 Fix: Interactive hover effect for the logout button
        logout_lbl = ctk.CTkLabel(text_frame, text="Log out", font=ctk.CTkFont(family=self.FONT_FAMILY, size=11), text_color=self.TEXT_SECONDARY, cursor="hand2")
        logout_lbl.pack(anchor="w", pady=0)
        
        # Hover effects to make it feel like a premium SaaS dashboard
        # Hover effects to make it feel like a premium SaaS dashboard
        logout_lbl.bind("<Enter>", lambda e: logout_lbl.configure(text_color=self.DANGER, font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, underline=True)))
        logout_lbl.bind("<Leave>", lambda e: logout_lbl.configure(text_color=self.TEXT_SECONDARY, font=ctk.CTkFont(family=self.FONT_FAMILY, size=11)))
        
        # 🔥 NEW: Trigger the logout sequence when clicked
        logout_lbl.bind("<Button-1>", lambda e: self._log_out())
        
        # ================= 2. EXPANDING SPACER =================
        # 🔥 Packed LAST. It will fill the gap between "OS Stats" and the "Bottom Container" safely!
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(side="top", fill="both", expand=True)
        # ================= TOP WORKSPACE BAR =================
        self.top_bar = ctk.CTkFrame(self.middle_column, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=(0, 30))

        # Status Pill
        # Status Pill
        self.status_pill = ctk.CTkLabel(
            self.top_bar, 
            text="● Not capturing", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="#9aa4b2", 
            fg_color="#0f1117", 
            corner_radius=999, 
            padx=18, 
            pady=8
        )
        self.status_pill.pack(side="left")

        # Timer
        self.timer_label = ctk.CTkLabel(
            self.top_bar, 
            text="", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color=self.TEXT_SECONDARY
        )
        self.timer_label.pack(side="left", padx=15)
        
        # Ambient/Breathing animations
        self.ambient_layer = ctk.CTkFrame(self.top_bar, height=2, fg_color=self.ACCENT_SOFT)
        self.ambient_layer.place(x=-300, y=0)
        self._add_status_breathing()
        self._start_ambient_motion()

        # ================= CAPTURE CARD =================
        self.capture_card = self._card()
        self.capture_card.pack(fill="x", pady=16)
        

        self.capture_header = ctk.CTkFrame(self.capture_card, fg_color=self.CARD)
        self.capture_header.pack(fill="x", padx=28, pady=(22, 6))

        self.capture_title = ctk.CTkLabel(
            self.capture_header,
            text="Live capture",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        self.capture_title.pack(side="left")

        self.capture_class_chip = ctk.CTkLabel(
            self.capture_header,
            text=self.current_class_title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.ACCENT_SOFT,
            fg_color="#0f1117",
            corner_radius=999,
            padx=14,
            pady=6,
            cursor="hand2"
        )
        self.capture_class_entry = ctk.CTkEntry(
            self.capture_header,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            fg_color="#0f1117",
            text_color=self.TEXT_PRIMARY,
             border_color=self.ACCENT,
        )    
        self.capture_class_chip.pack(side="right")
        self.capture_class_chip.bind("<Button-1>", self._enter_class_edit_mode)


        self.capture_desc = ctk.CTkLabel(
            self.capture_card,
            text="Start listening to your class and let me remember everything for you.",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_SECONDARY
        )
        self.capture_desc.pack(anchor="w", padx=28, pady=(0, 20))
        
        # 🔥 NEW: Horizontal Container for Buttons + Waveform
        self.capture_btns = ctk.CTkFrame(self.capture_card, fg_color="transparent")
        self.capture_btns.pack(fill="x", padx=28, pady=(0, 28))

        # Start Button
        self.start_btn = ctk.CTkButton(
            self.capture_btns,
            text="Start",
            height=44,
            width=100,
            corner_radius=12,
            fg_color=self.ACCENT,
            hover_color="#5855eb",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_capture,
            cursor="hand2"
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        # Stop Button
        self.stop_btn = ctk.CTkButton(
            self.capture_btns,
            text="Stop",
            height=44,
            width=100,
            corner_radius=12,
            fg_color=self.DISABLED, 
            hover_color="#ed5866",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.stop_capture,
            cursor="hand2"
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        # Mode Selector
        self.capture_mode_var = ctk.StringVar(value="Audio + Slides")
        self.capture_mode = "audio_video"
        mode_dropdown = ctk.CTkOptionMenu(
            self.capture_btns,
            values=["Audio + Slides", "Audio Only"],
            variable=self.capture_mode_var,
            command=self._update_capture_mode,
            width=140,
            height=44,
            corner_radius=12,
            fg_color="#1c192b",
            button_color="#1c192b",
            button_hover_color="#2f294d"
        )
        mode_dropdown.pack(side="left", padx=(0, 20))

        # Waveform animation label
        self.waveform = ctk.CTkLabel(
            self.capture_btns,
            text="▅ ▃ ▂ █ ▆ ▄ ▂ ▇ ▅ ▃ ▂", # Default static state
            font=("Consolas", 20),
            text_color=self.DISABLED
        )
        self.waveform.pack(side="left", expand=True, anchor="w")
        
        
        # ================= REVISION MODE CARD =================
        self.revision_card = self._card()
        self.revision_card.pack(fill="x", pady=(20, 12))
        

        self.revision_title = ctk.CTkLabel(
          self.revision_card,
    text="Revision Workspace",
    font=ctk.CTkFont(size=18, weight="bold"),
    text_color=self.TEXT_PRIMARY
)
        self.revision_title.pack(anchor="w", padx=28, pady=(22, 6))

        self.revision_desc = ctk.CTkLabel(
         self.revision_card,
    text="Analyze recordings, extract insights, and revise concepts in a focused environment.",
    font=ctk.CTkFont(size=14),
    text_color=self.TEXT_SECONDARY
)
        self.revision_desc.pack(anchor="w", padx=28, pady=(0, 18))

        self.open_revision_btn = ctk.CTkButton(
         self.revision_card,
    text="Open Revision Mode",
    height=48,
    width=220,
    corner_radius=12,
    fg_color=self.ACCENT,
    hover_color="#4338ca",
    text_color="#ffffff",
    font=ctk.CTkFont(size=15, weight="bold"),
    command=self.open_revision_workspace
)
        self.open_revision_btn.pack(anchor="w", padx=28, pady=(0, 22))


# ================= SYSTEM STATUS PANEL =================
        # ================= RIGHT PANEL: REVISION WORKSPACE =================
        # Put it in the right column!
        self.system_card = self._card(parent=self.right_column) 
        self.system_card.pack(fill="both", expand=True)

        right_header = ctk.CTkFrame(self.system_card, fg_color="transparent")
        right_header.pack(fill="x", padx=24, pady=(24, 10))
        
        ctk.CTkLabel(right_header, text="Revision Workspace", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(right_header, text="•••", font=ctk.CTkFont(size=18), text_color=self.TEXT_SECONDARY, cursor="hand2").pack(side="right")

        # The feed (formerly system_status_box)
        # The feed (formerly system_status_box)
        self.system_status_box = ctk.CTkTextbox(
            self.system_card,
            fg_color="#1d1936", # 🔥 Slightly lighter purple-glass to mimic bubbles
            text_color="#ffffff",
            corner_radius=14,
            font=("Inter", 14),
            wrap="word",
            border_color=self.BORDER,
            border_width=1
        )
        self.system_status_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.system_status_box.insert("end", "Welcome to your AI Study OS.\n\nI will track your session logs and transcript refinements here.")
        self.system_status_box.configure(state="disabled")

        # Fake Chat Input (Visual Match to Image)
        # Fake Chat Input (Visual Match to Image)
        # ================= REAL QUICK-CHAT (Restricted to Current Class) =================
        chat_input_container = ctk.CTkFrame(self.system_card, fg_color="#0a0910", corner_radius=24, border_width=1, border_color=self.BORDER)
        chat_input_container.pack(fill="x", padx=20, pady=(0, 24), ipady=2)
        
        ctk.CTkLabel(chat_input_container, text="•••", text_color=self.ACCENT, font=ctk.CTkFont(size=18)).pack(side="left", padx=(20, 10))
        
        self.quick_chat_entry = ctk.CTkEntry(
            chat_input_container,
            fg_color="transparent",
            border_width=0,
            placeholder_text="Ask about the current class...",
            placeholder_text_color=self.TEXT_SECONDARY,
            text_color=self.TEXT_PRIMARY,
            font=ctk.CTkFont(size=13)
        )
        self.quick_chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def ask_quick_chat():
            q = self.quick_chat_entry.get().strip()
            if not q: return
            
            # 1. Fetch the CURRENT active meeting folder only
            meeting_dir = self.storage.get_meeting_dir()
            if not meeting_dir:
                self._update_answer_box("⚠ No active class found. Start a capture or use the full Revision Workspace.")
                return
            
            # Get just the folder name (e.g., "2026-04-08_Biology") to pass to the engine
            meeting_name = os.path.basename(meeting_dir)
            
            # 2. Lock UI while processing
            self.quick_chat_entry.configure(state="disabled")
            quick_send_btn.configure(state="disabled")
            self._update_answer_box(f"Searching current class memory...\n")
            
            engine = self.ask_engine or AskEngine(base_data_dir="data")
            self.ask_engine = engine
            
            def run():
                try:
                    # 3. STRICT SCOPE: We pass ONLY the current meeting_name in a list!
                    stream_gen = engine.ask_stream(q, selected_meetings=[meeting_name])
                    
                    # Clear the "Searching..." text safely before streaming
                    self.after(0, lambda: self.system_status_box.configure(state="normal"))
                    self.after(0, lambda: self.system_status_box.delete("1.0", "end"))
                    self.after(0, lambda: self.system_status_box.configure(state="disabled"))
                    
                    # 4. Stream the real-time AI response into the right panel!
                    for token in stream_gen:
                        if token:
                            def append(t=token):
                                self.system_status_box.configure(state="normal")
                                self.system_status_box.insert("end", t)
                                self.system_status_box.see("end")
                                self.system_status_box.configure(state="disabled")
                            self.after(0, append)
                            
                except Exception as e:
                    self.after(0, lambda: self._update_answer_box(f"❌ Error: {str(e)}"))
                finally:
                    # Unlock UI safely
                    def cleanup():
                        self.quick_chat_entry.configure(state="normal")
                        self.quick_chat_entry.delete(0, "end")
                        quick_send_btn.configure(state="normal")
                    self.after(0, cleanup)

            threading.Thread(target=run, daemon=True).start()

        quick_send_btn = ctk.CTkButton(
            chat_input_container, 
            text="▶", 
            width=38, 
            height=38, 
            corner_radius=19, 
            fg_color=self.ACCENT, 
            hover_color=self.ACCENT_SOFT, 
            cursor="hand2",
            command=ask_quick_chat
        )
        quick_send_btn.pack(side="right", padx=6, pady=6)
        
        self.quick_chat_entry.bind("<Return>", lambda e: ask_quick_chat())



        threading.Thread(target=self._fade_in, daemon=True).start()
        threading.Thread(target=self._schedule_watcher, daemon=True).start() 
    # ================= CLASS EDITOR =================
    # ================= AUTHENTICATION UI =================
    def _build_login_screen(self):
        # Create a full-screen overlay that blocks the entire app
        self.login_overlay = ctk.CTkFrame(self, fg_color=self.BG)
        self.login_overlay.place(relwidth=1, relheight=1, relx=0, rely=0)
        self.login_overlay.lift()  # 🔥 FIX: Forces the lock screen ABOVE the dashboard

        

        # The sleek center card
        self.auth_card = ctk.CTkFrame(self.login_overlay, fg_color=self.CARD, corner_radius=20, border_color=self.BORDER, border_width=1, width=400, height=500)
        self.auth_card.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_card.pack_propagate(False)

        # Branding
        ctk.CTkLabel(self.auth_card, text="meetingSystem", font=ctk.CTkFont(family=self.FONT_FAMILY, size=28, weight="bold"), text_color=self.TEXT_PRIMARY).pack(pady=(40, 5))
        self.auth_subtitle = ctk.CTkLabel(self.auth_card, text="Login to your AI Study OS", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14), text_color=self.TEXT_SECONDARY)
        self.auth_subtitle.pack(pady=(0, 30))

        # Inputs
        self.user_entry = ctk.CTkEntry(self.auth_card, placeholder_text="Username", height=45, corner_radius=10, border_color=self.BORDER, font=ctk.CTkFont(size=14))
        self.user_entry.pack(fill="x", padx=40, pady=(0, 15))

        self.pass_entry = ctk.CTkEntry(self.auth_card, placeholder_text="Password", show="•", height=45, corner_radius=10, border_color=self.BORDER, font=ctk.CTkFont(size=14))
        self.pass_entry.pack(fill="x", padx=40, pady=(0, 20))

        self.auth_error_label = ctk.CTkLabel(self.auth_card, text="", text_color=self.DANGER, font=ctk.CTkFont(size=12, weight="bold"))
        self.auth_error_label.pack(pady=(0, 10))

        # Buttons
        self.action_btn = ctk.CTkButton(self.auth_card, text="Login", height=45, corner_radius=10, fg_color=self.ACCENT, hover_color="#4338ca", font=ctk.CTkFont(size=15, weight="bold"), command=self._handle_auth_action)
        self.action_btn.pack(fill="x", padx=40, pady=(0, 15))

        # Toggle state (Login vs Register)
        self.is_register_mode = False

        def toggle_mode():
            self.is_register_mode = not self.is_register_mode
            self.auth_error_label.configure(text="")
            if self.is_register_mode:
                self.auth_subtitle.configure(text="Create a new AI Brain account")
                self.action_btn.configure(text="Create Account")
                toggle_btn.configure(text="Already have an account? Login")
            else:
                self.auth_subtitle.configure(text="Login to your AI Study OS")
                self.action_btn.configure(text="Login")
                toggle_btn.configure(text="Need an account? Register")

        toggle_btn = ctk.CTkButton(self.auth_card, text="Need an account? Register", fg_color="transparent", hover_color=self.CARD, text_color=self.ACCENT_SOFT, font=ctk.CTkFont(size=13, underline=True), cursor="hand2", command=toggle_mode)
        toggle_btn.pack(pady=(5, 0))
        
        # Bind Enter key
        self.pass_entry.bind("<Return>", lambda e: self._handle_auth_action())

    def _handle_auth_action(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        
        self.auth_error_label.configure(text="")

        if self.is_register_mode:
            success, msg = self.auth.register(user, pwd)
            if success:
                self.auth_error_label.configure(text=msg, text_color=self.SUCCESS)
                # Auto switch back to login after 1.5 seconds
                self.after(1500, self._auto_switch_to_login, user)
            else:
                self.auth_error_label.configure(text=msg, text_color=self.DANGER)
        else:
            success, msg = self.auth.login(user, pwd)
            if success:
                self.current_user = user
                self._unlock_app()
            else:
                self.auth_error_label.configure(text=msg, text_color=self.DANGER)

    def _auto_switch_to_login(self, user):
        self.is_register_mode = False
        self.auth_subtitle.configure(text="Login to your AI Study OS")
        self.action_btn.configure(text="Login")
        self.user_entry.delete(0, "end")
        self.user_entry.insert(0, user)
        self.pass_entry.delete(0, "end")
        self.auth_error_label.configure(text="")

    def _unlock_app(self):
        # Destroy the lock screen to reveal the glorious dashboard beneath
        self.login_overlay.destroy()
        
        # Personalize the UI now that we know who is logged in!
        name = str(self.current_user or "User").capitalize()
        initials = name[:2].upper() # Grab the first two letters for the avatar
        
        self.brand_sub.configure(text=f"{name}'s AI Brain")
        self.profile_name_lbl.configure(text=name)
        self.avatar_lbl.configure(text=initials)
        
        self.show_system_notification("Access Granted", f"Welcome back, {name}!")
    def open_class_editor(self):
        self.editor = ctk.CTkToplevel(self)
        self.editor.title("Set Class Details")
        self.editor.geometry("420x440")
        self.editor.resizable(False, False)
        self.editor.configure(fg_color=self.BG)

        self.editor.transient(self)
        self.editor.grab_set()
        self.editor.focus_force()

        frame = ctk.CTkFrame(self.editor, fg_color=self.CARD, corner_radius=18, border_color=self.BORDER, border_width=1)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Clear X button ---
        self.clear_x_btn = ctk.CTkButton(
            frame,
            text="✕",
            width=32,
            height=32,
            fg_color="#1f2937",
            hover_color="#374151",
            text_color=self.TEXT_PRIMARY,
            corner_radius=16,
            command=self.clear_class_fields
        )
        self.clear_x_btn.place(relx=1.0, x=-16, y=16, anchor="ne")

        title_label = ctk.CTkLabel(frame, text="Set Class Details", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(anchor="w", padx=24, pady=(20, 12))

        ctk.CTkLabel(frame, text="Class Title", text_color=self.TEXT_SECONDARY).pack(anchor="w", padx=24)
        self.title_entry = ctk.CTkEntry(frame, height=38)
        self.title_entry.insert(0, self.current_class_title)
        self.title_entry.pack(fill="x", padx=24, pady=(6, 14))

        ctk.CTkLabel(frame, text="Meeting Link", text_color=self.TEXT_SECONDARY).pack(anchor="w", padx=24)
        self.link_entry = ctk.CTkEntry(frame, height=38)
        self.link_entry.insert(0, self.current_meeting_link)
        self.link_entry.pack(fill="x", padx=24, pady=(6, 14))

        ctk.CTkLabel(frame, text="Class Start Time (24h HH:MM)", text_color=self.TEXT_SECONDARY).pack(anchor="w", padx=24)
        self.time_entry = ctk.CTkEntry(frame, height=38, placeholder_text="14:30")
        if self.class_start_time:
            self.time_entry.insert(0, self.class_start_time)
        self.time_entry.pack(fill="x", padx=24, pady=(6, 20))

        btn_row = ctk.CTkFrame(frame, fg_color=self.CARD)
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

    

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="Save & Join",
            fg_color=self.ACCENT,
            hover_color="#4338ca",
            command=self.save_class_details
        )
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

    def clear_class_fields(self):
        self.title_entry.delete(0, "end")
        self.link_entry.delete(0, "end")
        self.time_entry.delete(0, "end")

    def join_meeting_only(self):
        link = self.link_entry.get().strip()
        if link:
            webbrowser.open(link)

    def save_class_details(self):
        self.current_class_title = self.title_entry.get().strip() or "Untitled Class"
        self.current_meeting_link = self.link_entry.get().strip()

        raw_time = self.time_entry.get().strip()
        if raw_time:
            try:
                datetime.strptime(raw_time, "%H:%M")
                self.class_start_time = raw_time
                self.class_triggered = False
            except ValueError:
                self.class_start_time = None
        else:
            self.class_start_time = None

        self.capture_class_chip.configure(text=self.current_class_title)
        self.editor.destroy()

        if self.current_meeting_link:
            webbrowser.open(self.current_meeting_link)
    def run_refinement_background(self):
     print("[Refinement] UI requested refinement")

     if not self.storage:
        print("[Refinement] Skipped: storage not initialized")
        return

     meeting_dir = self.storage.get_meeting_dir()
     print("[Refinement] meeting_dir =", meeting_dir)

     if not meeting_dir:
        print("[Refinement] Skipped: meeting_dir missing")
        return

     audio_path = os.path.join(meeting_dir, "audio_raw.wav")
     print("[Refinement] audio_path =", audio_path)

     if not os.path.exists(audio_path):
        print("[Refinement] Skipped: audio file not found")
        return

     if getattr(self, "_refinement_running", False):
        print("[Refinement] Already running → skipping")
        return

     self._refinement_running = True

     def task():
        try:
            print("[Refinement] Background thread started")

            # Show refining message safely
            self.after(0, lambda: self._update_answer_box(
                "Refining transcript...\nThis may take a moment."
            ))

            from refinement_engine import RefinementEngine

            engine = RefinementEngine(meeting_dir)
            engine.run()

            print("[Refinement] Refinement completed")

            # 🔥 BUILD INDEX HERE (AFTER refinement)
            self._build_final_index(meeting_dir)

            print("[Refinement] Index built")

            # Reload dashboard safely
            self.after(0, self.load_session_timeline)
            self.after(0, self.load_dashboard_stats)

            self.after(0, lambda: self._update_answer_box(
                "Class ready for revision.\nYou can now ask questions."
            ))

        except Exception as e:
            print("[Refinement] CRASHED:", e)
            self.after(0, lambda: self._update_answer_box(
                f"Refinement failed.\n{e}"
            ))

        finally:
            self._refinement_running = False

     threading.Thread(target=task, daemon=True).start()

    
    # ================= SCHEDULER =================

    def _schedule_watcher(self):
     while True:
        try:
            if (
                self.schedule_active
                and self.class_start_time
                and not self.class_triggered
            ):
                now = datetime.now().strftime("%H:%M")
                if now == self.class_start_time:
                    self.class_triggered = True

                    # If app is minimized → show system notification
                    if self.state() == "iconic":
                        self.show_system_notification(
                            "Class Started",
                            f"{self.current_class_title} is starting now.\nClick to respond."
                        )
                        self.root.after(1500, self._restore_and_prompt)
                    else:
                        # App is visible → show in-app popup
                        self.root.after(0, self.show_schedule_prompt)

            time.sleep(1)
        except Exception as e:
            print(f"[Scheduler Error] {e}")
            time.sleep(1)

    #======================================
        
    def show_schedule_prompt(self):
        if hasattr(self, "schedule_overlay"):
            try:
                self.schedule_overlay.destroy()
            except:
                pass

        # Always recreate overlay fresh
        self.schedule_overlay = ctk.CTkToplevel(self.root)
        self.schedule_overlay.attributes("-alpha", 0.0)
        self.schedule_overlay.attributes("-topmost", True)
        self.schedule_overlay.overrideredirect(True)
        self.schedule_overlay.configure(fg_color="#000000")
        self.schedule_overlay.attributes("-alpha", 0.9)
        self.schedule_overlay.geometry("1100x720+0+0")
        self.fade_in(self.schedule_overlay)

        card = ctk.CTkFrame(
            self.schedule_overlay,
            fg_color=self.CARD,
            corner_radius=18,
            border_color=self.BORDER,
            border_width=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(
            card,
            text="Class is about to start",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        title.pack(padx=24, pady=(20, 10))

        msg = ctk.CTkLabel(
            card,
            text="Do you want to start capturing now?",
            text_color=self.TEXT_SECONDARY
        )
        msg.pack(padx=24, pady=(0, 18))

        # Countdown label (NOW dynamic)
        self.countdown_label = ctk.CTkLabel(
            card,
            text="Auto starting in 10 seconds...",
            text_color=self.TEXT_SECONDARY,
            font=ctk.CTkFont(size=12)
        )
        self.countdown_label.pack(pady=(0, 12))

        btn_row = ctk.CTkFrame(card, fg_color=self.CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        start_btn = ctk.CTkButton(
            btn_row,
            text="Start Now",
            fg_color=self.ACCENT,
            hover_color="#4338ca",
            command=self._schedule_start_now
        )
        start_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        wait_btn = ctk.CTkButton(
            btn_row,
            text="Wait 2 min",
            fg_color="#1f2937",
            hover_color="#374151",
            command=self._schedule_wait
        )
        wait_btn.pack(side="left", expand=True, fill="x", padx=(8, 8))

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=self._schedule_cancel
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

        self.schedule_overlay.focus_force()

        # Start live countdown ticking
        self._update_countdown(10)

        # Auto-start after 10 seconds if no action
        self.auto_start_timer = self.after(10000, self._auto_start_capture)

    # ================= TOAST =================
    def _update_countdown(self, seconds):
        if not hasattr(self, "schedule_overlay"):
            return
        if seconds <= 0:
            return
        try:
            self.countdown_label.configure(
            text=f"⏳ Auto starting in {seconds} seconds...",
            text_color="#facc15" if seconds <= 5 else self.TEXT_SECONDARY
)

            self.after(1000, lambda: self._update_countdown(seconds - 1))
        except:
            pass
    def show_start_toast(self):
        if self.toast_active:
            return
        self.toast_active = True

        self.toast_overlay = ctk.CTkFrame(self, fg_color="#000000")
        self.toast_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.toast_card = ctk.CTkFrame(self.toast_overlay, fg_color=self.CARD, corner_radius=16)
        self.toast_card.place(relx=0.5, rely=0.2, anchor="center")

        msg = ctk.CTkLabel(self.toast_card,
                           text=f"{self.current_class_title} class started.\nStart capturing?",
                           font=ctk.CTkFont(size=16, weight="bold"),
                           text_color=self.TEXT_PRIMARY,
                           justify="center")
        msg.pack(padx=24, pady=(20, 12))

        btn_row = ctk.CTkFrame(self.toast_card, fg_color=self.CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        start_btn = ctk.CTkButton(btn_row, text="Start now", fg_color=self.ACCENT,
                                  hover_color="#4338ca", command=self._toast_start_now)
        start_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        not_now_btn = ctk.CTkButton(btn_row, text="Not now", fg_color="#1f2937",
                                    hover_color="#374151", command=self._toast_not_now)
        not_now_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

        threading.Thread(target=self._toast_auto_start, daemon=True).start()

    def _toast_auto_start(self):
        time.sleep(10)
        if self.toast_active:
            self.close_toast()
            self.start_capture()

    def _toast_start_now(self):
        self.close_toast()
        self.start_capture()

    def _toast_not_now(self):
        self.toast_card.destroy()

        choice_card = ctk.CTkFrame(self.toast_overlay, fg_color=self.CARD, corner_radius=16)
        choice_card.place(relx=0.5, rely=0.2, anchor="center")

        msg = ctk.CTkLabel(choice_card,
                           text="Do you want to cancel the schedule\nor extend the class time?",
                           font=ctk.CTkFont(size=15, weight="bold"),
                           justify="center")
        msg.pack(padx=24, pady=(20, 12))

        btn_row = ctk.CTkFrame(choice_card, fg_color=self.CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel schedule", fg_color="#1f2937",
                                   hover_color="#374151", command=lambda: self._cancel_schedule(choice_card))
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        extend_btn = ctk.CTkButton(btn_row, text="Extend 5 min", fg_color=self.ACCENT,
                                   hover_color="#4338ca", command=lambda: self._extend_schedule(choice_card))
        extend_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

    def _cancel_schedule(self, card):
        self.class_start_time = None
        self.toast_active = False
        card.destroy()
        self.toast_overlay.destroy()

    def _extend_schedule(self, card):
        if self.class_start_time:
            try:
                current_time = datetime.strptime(self.class_start_time, "%H:%M")
                new_time = (current_time + timedelta(minutes=5)).strftime("%H:%M")
                self.class_start_time = new_time
                self.class_triggered = False
            except ValueError:
                pass

        self.toast_active = False
        card.destroy()
        self.toast_overlay.destroy()

    def close_toast(self):
        self.toast_active = False
        self.toast_card.destroy()
        self.toast_overlay.destroy()

    def _schedule_start_now(self):
        try:
            if self.auto_start_timer:
                self.after_cancel(self.auto_start_timer)
        except:
            pass
        self.close_schedule_overlay()
        self.schedule_active = False
        self.class_triggered = True
        print("[Scheduler] User chose Start Now → Starting capture")        
        self.start_capture()

    def _schedule_wait(self):
       try:
           if self.auto_start_timer:
               self.after_cancel(self.auto_start_timer)
       except:
           pass
       self.close_schedule_overlay()
       new_time = datetime.now() + timedelta(minutes=2)
       self.class_start_time = new_time.strftime("%H:%M")
       self.class_triggered = False
       self.schedule_active = True
       self.class_source = "scheduled" 
       print("[Scheduler] User chose Wait 2 Minutes → Rescheduled to", self.class_start_time)        
        
    
    def _schedule_cancel(self):
         try:
             if self.auto_start_timer:
                    self.after_cancel(self.auto_start_timer)            
         except:
                pass
         self.close_schedule_overlay()
         
         self.schedule_active = False
         self.class_start_time = None
         self.class_triggered = False
         print("[Scheduler] Schedule cancelled by user")
            
    
     

    

    def _auto_start_capture(self):
     if self.schedule_active and not self.is_capturing and not self.class_triggered:
         print("[Scheduler] Auto starting capture")
         self._schedule_start_now()
        

    

    #===============NOTIFICATON POPUP=================
    def show_system_notification(self, title, message):
        try:
            toaster = ToastNotifier()  
            toaster.show_toast(
                title=title,
                msg=message,
                duration=10,
                threaded=True,
                callback_on_click=self._restore_and_prompt
            )
        except Exception as e:
            print("[Notification Error]", e)
   

    def _restore_and_prompt(self):
        try:
         self.deiconify()
         self.lift()
         self.focus_force()
         self.after(300, self.show_schedule_prompt)
        except Exception as e:
         print("[ Restore Error]", e)


    # ================= DASHBOARD OVERLAY =================

    def open_dashboard_overlay(self):

    # Destroy existing overlay safely
     if hasattr(self, "dash_overlay"):
        try:
            self.dash_overlay.destroy()
        except:
            pass

    # Fullscreen overlay
     self.dash_overlay = ctk.CTkFrame(self, fg_color="#000000")
     self.dash_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Main card
     self.dash_card = ctk.CTkFrame(
        self.dash_overlay,
        fg_color=self.CARD,
        corner_radius=18,
        border_color=self.BORDER,
        border_width=1,
        width=720,
        height=680
    )
     self.dash_card.place(relx=0.5, rely=0.5, anchor="center")
     self.dash_card.pack_propagate(False)
     self._dashboard_meeting_dir = self.storage.get_meeting_dir()

    # Close button (top right)
     close_x = ctk.CTkButton(
        self.dash_card,
        text="✕",
        width=32,
        height=32,
        fg_color="#1f2937",
        hover_color="#374151",
        text_color=self.TEXT_PRIMARY,
        corner_radius=16,
        command=self.close_dashboard_overlay
    )
     close_x.place(relx=1.0, x=-14, y=14, anchor="ne")

    # ================= HEADER =================
     header_frame = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     header_frame.pack(fill="x", padx=28, pady=(24, 12))

     title_text = self.current_class_title or "Untitled Class"

     self.session_title_label = ctk.CTkLabel(
        header_frame,
        text=title_text,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=self.TEXT_PRIMARY
    )
     self.session_title_label.pack(anchor="w")

     self.session_meta_label = ctk.CTkLabel(
         header_frame,
        text="Session details loading...",
        text_color=self.TEXT_SECONDARY,
        font=ctk.CTkFont(size=12)
    )
     self.session_meta_label.pack(anchor="w", pady=(4, 0))

    # ================= STATS =================
     self.stats_label = ctk.CTkLabel(
        self.dash_card,
        text="Loading stats...",
        text_color=self.TEXT_PRIMARY,
        font=ctk.CTkFont(size=14),
        justify="left"
    )
     self.stats_label.pack(anchor="w", padx=28, pady=(6, 18))

    # ================= SEARCH =================
     search_frame = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     search_frame.pack(fill="x", padx=28, pady=(0, 12))

     self.search_var = ctk.StringVar()

     self.search_entry = ctk.CTkEntry(
        search_frame,
        placeholder_text="Search transcript...",
        textvariable=self.search_var
    )
     self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

     self.search_prev_btn = ctk.CTkButton(
        search_frame,
        text="◀",
        width=40,
        command=self._search_prev
    )
     self.search_prev_btn.pack(side="left", padx=4)

     self.search_next_btn = ctk.CTkButton(
        search_frame,
        text="▶",
        width=40,
        command=self._search_next
    )
     self.search_next_btn.pack(side="left", padx=4)

     self.search_entry.bind("<Return>", lambda e: self._run_search())
     self.search_entry.bind("<KeyRelease>", self._on_search_typing)

    # ================= TIMELINE =================
    # ================= CONTENT AREA (Scrollable Safe Zone) =================
     content_frame = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     content_frame.pack(fill="both", expand=True, padx=28, pady=(0, 12))
     content_frame.pack_propagate(False)

     ctk.CTkLabel(
        self.dash_card,
        text="Session Timeline",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=self.TEXT_PRIMARY
    ).pack(anchor="w", padx=28, pady=(6, 6))

     self.timeline_box = ctk.CTkTextbox(
        content_frame,
        #height=250,
        fg_color="#0b1220",
        text_color=self.TEXT_PRIMARY,
        border_color=self.BORDER,
        border_width=1,
        corner_radius=10,
        wrap="word"
    )
     self.timeline_box.pack(fill="both", expand=True, pady=(0, 12))

     self.timeline_box.configure(state="disabled")

    # ================= BOOKMARKS =================
     self.bookmark_box = ctk.CTkTextbox(
        content_frame,
        height=80,
        fg_color="#0b1220",
        text_color=self.TEXT_PRIMARY,
        border_color=self.BORDER,
        border_width=1,
        corner_radius=10
    )
     self.bookmark_box.pack(fill="x", padx=28, pady=(0, 12))
     self.bookmark_box.configure(state="disabled")

     self._render_bookmarks()
    # ================= SEEK ROW =================
     seek_row = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     seek_row.pack(fill="x", padx=28, pady=(0, 12))

     self.seek_var = ctk.DoubleVar(value=0.0)

     duration = int(self._audio_duration_sec or 1)


     self.seek_slider = ctk.CTkSlider(
       seek_row,
       from_=0,
       to=duration,
       variable=self.seek_var,
      command=self._on_seek_change
)
     self.seek_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

     self.time_label = ctk.CTkLabel(
      seek_row,
      text="00:00 / 00:00",
      text_color="#9ca3af",
      width=110
)
     self.time_label.pack(side="right")

     self.seek_slider.bind("<ButtonRelease-1>", self._on_seek_commit)

    # ================= CONTROLS =================
     control_row = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     control_row.pack(fill="x", padx=28, pady=(0, 14))

     self.play_btn = ctk.CTkButton(
        control_row,
        text="▶ Play",
        fg_color=self.ACCENT,
        command=self._audio_play
    )
     self.play_btn.pack(side="left", padx=(0, 8))

     self.pause_btn = ctk.CTkButton(
        control_row,
        text="⏸ Pause",
        fg_color="#1f2937",
        command=self._audio_pause
    )
     self.pause_btn.pack(side="left", padx=(0, 16))

     self.bookmark_btn = ctk.CTkButton(
        control_row,
        text="🔖 Bookmark",
        fg_color="#1f2937",
        command=self.add_bookmark
    )
     self.bookmark_btn.pack(side="left", padx=(0, 16))

     speed_frame = ctk.CTkFrame(control_row, fg_color=self.CARD)
     speed_frame.pack(side="left")

     for label, rate in [("0.75x", 0.75), ("1x", 1.0), ("1.25x", 1.25), ("1.5x", 1.5), ("2x", 2.0)]:
        btn = ctk.CTkButton(
            speed_frame,
            text=label,
            width=60,
            fg_color="#1f2937",
            command=lambda r=rate: self._set_playback_speed(r)
        )
        btn.pack(side="left", padx=4)

    # ================= FOOTER =================
     footer_row = ctk.CTkFrame(self.dash_card, fg_color=self.CARD)
     footer_row.pack(fill="x", padx=28, pady=(0, 12))

     close_btn = ctk.CTkButton(
        footer_row,
        text="Close",
        fg_color="#1f2937",
        command=self.close_dashboard_overlay
    )
     close_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

     refresh_btn = ctk.CTkButton(
        footer_row,
        text="Refresh",
        fg_color=self.ACCENT,
        command=self._refresh_dashboard_now
    )
     refresh_btn.pack(side="left", expand=True, fill="x", padx=(8, 8))

     export_btn = ctk.CTkButton(
        footer_row,
        text="Export",
        fg_color="#1f2937",
        command=self.export_session
    )
     export_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

    # ================= LOAD DATA =================
     self.load_dashboard_stats()
     self.load_session_timeline()

    # Restore playback memory
     if getattr(self, "_last_playback_pos", 0) > 0:
        self._playback_pos = self._last_playback_pos

     if getattr(self, "_was_playing", False):
        self.after(300, self._audio_play)

 

 

      
        # -------- Session Timeline --------

        
     

       

    def close_schedule_overlay(self):
     if hasattr(self, "schedule_overlay"):
        try:
            self.schedule_overlay.destroy()
        except:
            pass
    def refresh_dashboard_stats(self):
     if hasattr(self, "dash_card") and self.dash_card.winfo_exists():
        self.load_dashboard_stats()
        self.after(2000, self.refresh_dashboard_stats)
    
    def fade_in(self, widget, step=0.05):
        try:
            current = widget.attributes("-alpha")
            if current < 1.0:
             widget.attributes("-alpha", current + step)
            self.after(15, lambda: self.fade_in(widget, step))
        except:
            pass

    def load_dashboard_stats(self):
     # 🔥 Check if the window was closed to prevent Tkinter crashes
     if not hasattr(self, "stats_label") or not self.stats_label.winfo_exists():
      return   
        
     try:
        if not self.storage or not self.storage.meeting_dir:
            self.stats_label.configure(text="No active session yet.")
            return

        audio_file = os.path.join(self.storage.meeting_dir, "audio_notes.json")

        if not os.path.exists(audio_file):
            self.stats_label.configure(text="No data captured yet.")
            return

        with open(audio_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        total = len(data)
        audio_count = total  # only audio for now
        last_time = data[-1]["time"] if data else "N/A"

        self.stats_label.configure(
            text=(
                f"Total Entries: {total}\n"
                f"Audio: {audio_count}\n"
                f"Last Entry: {last_time}"
            )
        )

     except Exception as e:
        self.stats_label.configure(text=f"Failed to load stats: {e}")


    def _refresh_dashboard_now(self):
     self.load_dashboard_stats()
     self.load_session_timeline()

    # ================= SCHEDULE OVERLAY =================

    def open_schedule_overlay(self):
    # Always create overlay first
     self.schedule_overlay = ctk.CTkFrame(self, fg_color="#000000")
     self.schedule_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

     self.schedule_card = ctk.CTkFrame(
        self.schedule_overlay,
        fg_color=self.CARD,
        corner_radius=18,
        border_color=self.BORDER,
        border_width=1
    )
     self.schedule_card.place(relx=0.5, rely=0.5, anchor="center")

     title = ctk.CTkLabel(
        self.schedule_card,
        text="Schedule Class",
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=self.TEXT_PRIMARY
    )
     title.pack(anchor="w", padx=28, pady=(24, 12))

     desc = ctk.CTkLabel(
        self.schedule_card,
        text="Set up automatic class capture.",
        text_color=self.TEXT_SECONDARY,
        justify="left",
        wraplength=420
    )
     desc.pack(anchor="w", padx=28, pady=(0, 24))

     ctk.CTkLabel(
        self.schedule_card,
        text="Class Title",
        text_color=self.TEXT_SECONDARY
    ).pack(anchor="w", padx=28)

     self.schedule_title_entry = ctk.CTkEntry(
        self.schedule_card,
        height=38,
        placeholder_text="e.g., Biology 101"
    )
     self.schedule_title_entry.pack(fill="x", padx=28, pady=(6, 16))

     ctk.CTkLabel(
        self.schedule_card,
        text="Meeting Link",
        text_color=self.TEXT_SECONDARY
    ).pack(anchor="w", padx=28)

     self.schedule_link_entry = ctk.CTkEntry(
        self.schedule_card,
        height=38,
        placeholder_text="https://meet.google.com/..."
    )
     self.schedule_link_entry.pack(fill="x", padx=28, pady=(6, 16))

     ctk.CTkLabel(
        self.schedule_card,
        text="Start Time (24h format)",
        text_color=self.TEXT_SECONDARY
    ).pack(anchor="w", padx=28)

     self.schedule_time_entry = ctk.CTkEntry(
        self.schedule_card,
        height=38,
        placeholder_text="14:30"
    )
     self.schedule_time_entry.pack(fill="x", padx=28, pady=(6, 24))

     btn_row = ctk.CTkFrame(self.schedule_card, fg_color=self.CARD)
     btn_row.pack(fill="x", padx=28, pady=(0, 24))

     save_btn = ctk.CTkButton(
        btn_row,
        text="Save & Schedule",
        fg_color=self.ACCENT,
        hover_color="#4338ca",
        command=self.save_schedule_details
    )
     save_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

     close_btn = ctk.CTkButton(
        btn_row,
        text="Close",
        fg_color="#1f2937",
        hover_color="#374151",
        command=self.close_schedule_overlay
    )
     close_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

     #shared helper
    def _create_schedule_overlay(self):
     if hasattr(self, "schedule_overlay") and self.schedule_overlay.winfo_exists():
        self.schedule_overlay.destroy()

        self.schedule_overlay = ctk.CTkFrame(self, fg_color="#000000")
        self.schedule_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)


    def save_schedule_details(self):
     # Read values
      self.current_class_title = self.schedule_title_entry.get().strip() or "Untitled Class"
      self.current_meeting_link = self.schedule_link_entry.get().strip()

      raw_time = self.schedule_time_entry.get().strip()
      if raw_time:
        try:
            datetime.strptime(raw_time, "%H:%M")
            self.class_start_time = raw_time
            self.class_triggered = False
            self.schedule_active = True 
        except ValueError:
            self.class_start_time = None
      else:
        self.class_start_time = None
        self.capture_class_chip.configure(text=self.current_class_title)
        self.close_schedule_overlay()

    # Mark this class as scheduled (not manual)
      self.class_source = "scheduled"
      self.schedule_active = True

    # Update UI chip
      self.capture_class_chip.configure(text=self.current_class_title)

    # Close overlay
      self.close_schedule_overlay()

    # Open meeting immediately (capture will NOT start)
      if self.current_meeting_link:
        import webbrowser
        webbrowser.open(self.current_meeting_link)


    # ================= AMBIENT =================

    def _start_ambient_motion(self):
        def move():
            while True:
                for x in range(-300, 1300, 2):
                    self.ambient_layer.place(x=x, y=0)
                    time.sleep(0.01)
                time.sleep(2)

        threading.Thread(target=move, daemon=True).start()

    def _add_status_breathing(self):
        def breathe():
            while True:
                self.status_pill.configure(fg_color="#151a2e")
                time.sleep(1.6)
                self.status_pill.configure(fg_color=self.CARD)
                time.sleep(1.6)

        threading.Thread(target=breathe, daemon=True).start()

    def _fade_in(self):
        for i in range(0, 101, 4):
            self.attributes("-alpha", i / 100)
            time.sleep(0.01)

    # ================= TIMER =================
    def _animate_waveform(self):
        import random
        bars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        while self.is_capturing:
            wave = "".join(random.choice(bars) for _ in range(12))
            try:
                self.waveform.configure(text=wave, text_color="#00e5ff")
                time.sleep(0.08)
            except:
                break
        try:
            self.waveform.configure(text="▂ ▂ ▂ ▂ ▂ ▂ ▂ ▂ ▂ ▂ ▂ ▂", text_color=self.DISABLED)
        except:
            pass
    def _run_timer(self):
        if self.start_time is None:
            return

        while self.timer_running:
            elapsed = int(time.time() - self.start_time)
            hrs = elapsed // 3600
            mins = (elapsed % 3600) // 60
            secs = elapsed % 60
            self.timer_label.configure(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
            time.sleep(1)

    # ================= HELPERS =================

    def _card(self, parent=None):
        # Defaults to middle_column, but allows us to put cards in the right column!
        target_parent = parent if parent else getattr(self, 'middle_column', self.root)
        return ctk.CTkFrame(
            target_parent,
            fg_color=self.CARD,
            corner_radius=20,
            border_color=self.BORDER, 
            border_width=1
        )

    ...
    #==============LOGIC==================
    def start_capture(self):

     if self.is_capturing:
        return

     title = self.current_class_title or "Untitled Class"
     self.storage.start_new_meeting(title)

     print("[UI] Active meeting set to", self.storage.get_meeting_dir())

    # Step 1 → Select target window
     self._open_window_selector(
        on_confirm_callback=self._start_capture_after_window
    )


    def stop_capture(self):
    # self.ask_btn.configure(state="normal")   
        
     if not self.is_capturing:
        return

     self.is_capturing = False
     self.timer_running = False
     self._live_polling = False

    # Stop audio engine FIRST (flush WAV safely)
     if self.audio_engine is not None:
        try:
            self.audio_engine.stop()
        except Exception as e:
            print("[UI] Audio stop error:", e)
        finally:
            self.audio_engine = None

    # Prevent double refinement
     

     self.status_pill.configure(text="Not capturing", text_color=self.TEXT_SECONDARY)
     self.timer_label.configure(text="")

     self.start_btn.configure(state="normal")
     self.stop_btn.configure(state="disabled", fg_color=self.DISABLED, hover_color="#4b5563")

     self.system_status_box.configure(state="normal")
     self.system_status_box.delete("1.0", "end")
     if self.capture_mode == "audio_video":
       msg = "✅ Class saved.\n\nRefining transcript and slides..."
     else:
       msg = "✅ Recording saved.\n\nRefining transcript..."

     self.system_status_box.insert("end", msg)
     self.system_status_box.configure(state="disabled")

    # Start refinement AFTER audio is fully stopped
     meeting_dir = self.storage.get_meeting_dir()
     self.run_refinement_background()
     

     
     self.system_status_box.configure(state="normal")
     self.system_status_box.delete("1.0", "end")
     if self.capture_mode == "audio_video":
      msg = "✅ Class ready.\nSlides + transcript indexed.\nYou can ask questions now."
     else:
      msg = "✅ Recording ready.\nTranscript indexed.\nYou can ask questions now."

     self.system_status_box.insert("end", msg)
     self.system_status_box.configure(state="disabled")


    
    def _enter_class_edit_mode(self, event=None):
        self.capture_class_chip.pack_forget()

        self.capture_class_entry.delete(0, "end")
        self.capture_class_entry.insert(0, self.current_class_title)

        self.capture_class_entry.pack(side="right")
        self.capture_class_entry.focus()
        self.capture_class_entry.bind("<Return>", self._save_class_name)

    def _save_class_name(self, event=None):
     value = self.capture_class_entry.get().strip()

     if value:
        self.current_class_title = value
        self.capture_class_chip.configure(text=value)

        self.capture_class_entry.pack_forget()
        self.capture_class_chip.pack(side="right")
        
    def _run_live_poll(self):
     if not getattr(self, "_live_polling", False):
        return
    
    
     self._poll_live_transcript()
     self.after(1000, self._run_live_poll)
    


    def _extract_classes_from_question(self, question: str):
       import re
       return re.findall(r"@([A-Za-z0-9_-]+)", question)
      
  
    def load_session_timeline(self):
     if not hasattr(self, "timeline_box"):
       return  

     self._live_search_enabled = False
     self._timeline_entries = []
     self._search_matches = []
     self._search_index = -1
     self._timeline_tags = {}
     self._word_timeline = []

     try:
        print("[Dashboard] load_session_timeline called")

        if not self.storage:
            print("[Dashboard] No storage object")
            self._render_empty_timeline("No session active.")
            return

        data = self.storage.load_best_timeline()
        print("[Dashboard] Loaded entries count =", len(data))

        # ❌ REMOVE old count optimization completely
        # DO NOT skip rendering — dashboard must always rebuild UI

        self.timeline_box.configure(state="normal")
        self.timeline_box.delete("1.0", "end")

        if not data:
            self.timeline_box.insert("end", "No transcript available yet.\n\n")
            self.timeline_box.insert("end", "• Try recording some audio\n")
            self.timeline_box.insert("end", "• Or wait for refinement to finish\n")
        else:
            last_minute = None
            textbox = self.timeline_box._textbox  # internal tk textbox

            for entry in data:
                time_str = entry.get("time", "??:??:??")
                text = entry.get("text", "").strip()
                elapsed = entry.get("elapsed", None)
                print("DEBUG elapsed raw value:", elapsed, "type:", type(elapsed))


                if not text:
                    continue

                # Group by minute
                minute = time_str[:5] if ":" in time_str else None
                if minute != last_minute:
                    textbox.insert("end", f"\n── {minute} ──\n")
                    last_minute = minute

                start_index = textbox.index("end-1c")
                textbox.insert("end", f"[{time_str}] {text}\n\n")
                end_index = textbox.index("end-1c")

                if elapsed is None:
                    continue

                tag_name = f"line_{len(self._timeline_entries)}"

                start_sec = float(elapsed)
                duration = max(0.4, len(text.split()) * 0.25)
                end_sec = start_sec + duration

                self._word_timeline.append((start_sec, end_sec, tag_name))
                self._timeline_entries.append((start_sec, tag_name))
                self._timeline_tags[tag_name] = start_sec

                # Apply tag styling
                textbox.tag_add(tag_name, start_index, end_index)
                textbox.tag_configure(
                    tag_name,
                    foreground="#93c5fd",
                    underline=True
                )
                # 🔥 DOUBLE CLICK to play from exact timestamp
                textbox.tag_bind(
    tag_name,
    "<Double-Button-1>",
    lambda e, s=start_sec: self._play_audio_from_elapsed(float(s))
)


        self.timeline_box.configure(state="disabled")

     except Exception as e:
        print("[Dashboard Timeline Error]", e)

        try:
            self.timeline_box.configure(state="normal")
            self.timeline_box.delete("1.0", "end")
            self.timeline_box.insert(
                "end", "Failed to load timeline.\nPlease retry."
            )
            self.timeline_box.configure(state="disabled")
        except Exception:
            pass
        self._live_search_enabled = False

    def _run_live_indexer(self):
        if not self.is_capturing:
            return

        meeting_dir = self.storage.get_meeting_dir()
        if meeting_dir:
            try:
                from rag.chunker import TranscriptChunker
                from rag.index_builder import MeetingIndexBuilder

                # 1. Build fresh chunks from the rolling transcript.json
                chunker = TranscriptChunker(meeting_dir)
                chunker.build_live_chunks()

                # 2. Build a temporary live FAISS index
                builder = MeetingIndexBuilder(meeting_dir)
                builder.build_live_index()

                # 3. Tell the AskEngine to use the newly generated live index
                if hasattr(self, 'ask_engine') and self.ask_engine:
                    self.ask_engine.clear_cache(meeting_dir)

            except Exception as e:
                print(f"[Live Indexer Error] {e}")

        # Loop this every 15 seconds as long as we are capturing
        self.after(15000, self._run_live_indexer)
    def _poll_live_transcript(self):
        # We removed the Live Transcript UI box, so this function is intentionally blank.
        pass
        
    def close_dashboard_overlay(self):

    # Save playback position before closing
     if self._playback_audio is not None and self._playback_rate:
        self._last_playback_pos = self._playback_pos

     self._stop_audio_stream()

     try:
        self.dash_card.destroy()
        self.dash_overlay.destroy()
     except:
        pass


    
    def _set_timeline_text(self, text):
     self.timeline_box.configure(state="normal")
     self.timeline_box.delete("1.0", "end")
     self.timeline_box.insert("end", text)
     self.timeline_box.configure(state="disabled")
 
    def _render_empty_timeline(self, message: str):
     try:
        self.timeline_box.configure(state="normal")
        self.timeline_box.delete("1.0", "end")
        self.timeline_box.insert("end", message)
        self.timeline_box.configure(state="disabled")
     except:
        pass
    
    """ def search_timeline(self):
     query = self.search_entry.get().strip().lower()
     if not query:
        self.load_session_timeline()
        return

     data = self.storage.load_best_timeline()

     results = []
     for entry in data:
        text = entry.get("text", "").lower()
        if query in text:
            results.append(entry)

     self.timeline_box.configure(state="normal")
     self.timeline_box.delete("1.0", "end")

     if not results:
        self.timeline_box.insert("end", "No matching results found.")
     else:
        for entry in results:
            self.timeline_box.insert(
                "end",
                f"[{entry.get('time')}] {entry.get('text')}\n\n"
            )

     self.timeline_box.configure(state="disabled") """
     
    

    def export_session(self):
     data = self.storage.load_best_timeline()
     if not data:
        return

     file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")]
    )

     if not file_path:
        return

     with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(f"[{entry.get('time')}] {entry.get('text')}\n")

     print("[Dashboard] Exported transcript to", file_path)
     
   
    def _parse_time_to_seconds(self, time_str: str) -> int:
     try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
     except:
        return 0


    
        
    
    def _get_default_output_device(self):
     try:
        # Force-cast because sounddevice stubs are wrong
        from typing import Dict, Any, cast

        devices = cast(list[Dict[str, Any]], sd.query_devices())
        default_output = sd.default.device[1]  # (input, output)

        # Prefer system default output device
        if default_output is not None:
            idx = int(default_output)
            if 0 <= idx < len(devices):
                dev = devices[idx]
                name = str(dev["name"]) if "name" in dev else f"Device {idx}"
                print("[Audio Player] Using default output device:", name)
                return idx

        # Fallback: first output-capable device
        for i in range(len(devices)):
            dev = devices[i]

            if not isinstance(dev, dict):
                continue

            max_out_raw = dev.get("max_output_channels", 0)
            try:
                max_out = int(max_out_raw)
            except Exception:
                max_out = 0

            if max_out > 0:
                name = str(dev["name"]) if "name" in dev else f"Device {i}"
                print("[Audio Player] Fallback output device:", name)
                return i

     except Exception as e:
        print("[Audio Player] Device query error:", e)

     return None
    
   
   
        
    def _highlight_timeline_tag(self, tag_name: str):
     for tag in self._timeline_tags.keys():
        self.timeline_box._textbox.tag_configure(tag, background="")

     if isinstance(tag_name, str):
      self._clear_active_transcript_highlight()

      self._active_transcript_tag = tag_name
 
     
    
    
    

    def _pause_audio(self):
     print("[Audio Player] Pause requested")

     if not self._is_playing:
        return

     self._stop_audio_stream()


    def _resume_audio(self):
     print("[Audio Player] Resume requested")

     if self._playback_audio is None or self._playback_rate is None:
        print("[Audio Player] No audio loaded to resume")
        return

     if self._is_playing:
        return

     device_index = self._get_default_output_device()

     
    def _play_audio_from_elapsed(self, elapsed_seconds: float, play_duration: Optional[float] = None, meeting_dir: Optional[str] = None):
        if self._is_seeking: return
        self._is_seeking = True
        self._set_playback_state("seeking")

        try:
            # 🔥 NEW: If we clicked a different meeting, force reload the audio file
            if meeting_dir:
                expected_path = os.path.join(meeting_dir, "audio_raw.wav")
                if getattr(self, "_current_audio_path", None) != expected_path:
                    self._playback_audio = None  # Clear old audio
                    self._current_audio_path = expected_path

            if self._playback_audio is None:
                self._load_audio_for_playback(explicit_meeting_dir=meeting_dir)
                
            if self._playback_audio is None:
                print("[Audio Player] Audio still not available after load attempt")
                return
            if self._playback_audio is None or self._playback_rate is None:
                self._set_playback_state("idle")
                return

            self._stop_audio_stream()
            total_frames = len(self._playback_audio)
            
            new_pos = int(float(elapsed_seconds) * self._playback_rate)
            self._playback_pos = max(0, min(new_pos, total_frames - 1))
            
            if play_duration is not None:
                self._stop_playback_pos = self._playback_pos + int(play_duration * self._playback_rate)
            else:
                self._stop_playback_pos = None

            print(f"[Audio Player] Playing from {round(elapsed_seconds, 2)}s")

            self._set_playback_state("playing")
            self.after(0, self._audio_play)
        except Exception as e:
            print("[Audio Player Error]", e)
            self._set_playback_state("idle")
        finally:
            self._is_seeking = False


       


    def _audio_play(self):

    # 🔒 Must have audio loaded
     if self._playback_audio is None or self._playback_rate is None:
        print("[Audio Player] No audio loaded")
        return

    # Already playing → do nothing
     if self._playback_stream is not None:
        return

    # ✅ Resume only if NOT currently seeking
     if (
        getattr(self, "_last_playback_pos", 0) > 0
        and self._pending_seek_pos is None
        and not getattr(self, "_is_seeking", False)
    ):
         self._playback_pos = self._last_playback_pos

     device_index = self._get_default_output_device()

     def callback(outdata, frames, time_info, status):
            try:
                if status: print("[Audio Player] Stream status:", status)
                if self._playback_audio is None:
                    outdata.fill(0)
                    return

                if self._pending_seek_pos is not None:
                    self._playback_pos = int(self._pending_seek_pos)
                    self._pending_seek_pos = None

                start = int(self._playback_pos)
                total_frames = len(self._playback_audio)

                # 🔥 FIX: Grab it into a local variable so Pylance can verify the type
                stop_pos = getattr(self, "_stop_playback_pos", None)

                # Auto-pause if we hit the limit
                if stop_pos is not None and start >= stop_pos:
                    outdata.fill(0)
                    self._stop_playback_pos = None  # Reset limit
                    self.after(0, self._audio_pause) # Trigger UI pause
                    return

                if start >= total_frames:
                    outdata.fill(0)
                    self.after(0, self._stop_audio_stream)
                    return

                # Calculate end chunk, safely respecting the stop position
                end = min(start + frames, total_frames)
                if stop_pos is not None:
                    end = min(end, stop_pos)

                chunk = self._playback_audio[start:end]

                outdata.fill(0)
                outdata[:len(chunk)] = chunk

                speed = float(self._playback_speed)
                step = max(1, int(frames * speed))
                self._playback_pos += step

                self._schedule_ui_update()
            except Exception as e:
                print("[Audio Callback Error]", e)
                outdata.fill(0)
                self.after(0, self._stop_audio_stream)

     self._playback_stream = sd.OutputStream(
        samplerate=self._playback_rate,
        channels=2,
        dtype="float32",
        device=device_index,
        callback=callback,
        blocksize=1024
    )

     self._playback_stream.start()
     self._is_playing = True

     self._update_play_pause_ui()



    
    
    def _audio_pause(self):
    # 🔒 Only one truth
     if self._playback_stream is None:
        print("[Audio Player] Already paused")
        return

     print("[Audio Player] Pausing playback")
     self._stop_audio_stream()
     self._update_play_pause_ui()



    def _stop_audio_stream(self):
     self._was_playing = self._playback_stream is not None
     stream = self._playback_stream

    # ✅ SAVE CURRENT POSITION BEFORE STOPPING
     if self._playback_rate and isinstance(self._playback_rate, (int, float)):
        self._last_playback_pos = self._playback_pos

     if stream is None:
        return

     try:
        stream.stop()
        stream.close()
        print("[Audio Player] Stream stopped cleanly")
     except Exception as e:
        print("[Audio Player] Stream stop error:", e)

     self._playback_stream = None
     self._is_playing = False



  


    def _update_seek_slider(self):

     if (
        self._playback_audio is None
        or self._playback_rate is None
        or not hasattr(self, "seek_var")
    ):
        return

     rate = float(self._playback_rate)
     if rate <= 0:
        return

     current_sec = self._playback_pos / rate
     total_sec = float(self._audio_duration_sec or 0)

     if total_sec > 0:
        current_sec = max(0.0, min(current_sec, total_sec))

     self.seek_var.set(current_sec)

     self.time_label.configure(
        text=f"{self._format_time(int(current_sec))} / {self._format_time(int(total_sec))}"
    )


    def _update_play_pause_ui(self):
     playing = self._playback_stream is not None

     if playing:
        self.play_btn.configure(fg_color="#1f2937")
        self.pause_btn.configure(fg_color=self.ACCENT)
     else:
        self.play_btn.configure(fg_color=self.ACCENT)
        self.pause_btn.configure(fg_color="#1f2937")

        
    def _format_time(self, seconds: float | int) -> str:
     seconds = int(seconds)
     mins = seconds // 60
     secs = seconds % 60
     return f"{mins:02d}:{secs:02d}"
 
     
    def _highlight_current_transcript(self):
     if not hasattr(self, "_timeline_entries"):
        return
    # If user is browsing search results, do not override highlight
     if getattr(self, "_search_index", -1) >= 0 and not self._is_playing:
      return

    # 🔒 Playback highlight overrides search highlight
     self._clear_active_transcript_highlight()


     self._active_transcript_tag = None

 

     rate = int(self._playback_rate or 0)
     if rate <= 0:
        return

     current_sec = self._playback_pos // rate
     active_tag = None

     entries = self._timeline_entries
     if not entries:
      return

# Binary-style linear clamp
     for i in range(len(entries) - 1):
      start_sec, tag = entries[i]
      next_start, _ = entries[i + 1]

      if start_sec <= current_sec < next_start:
        active_tag = tag
        break
      else:
       active_tag = entries[-1][1]


     if not active_tag:
        return

     if getattr(self, "_last_active_tag", None) == active_tag:
        return

    # 🔥 ONLY clear previous
     last = getattr(self, "_last_active_tag", None)
     if last:
        self._clear_active_transcript_highlight()


     self.timeline_box._textbox.tag_configure(
        active_tag,
        background="#1e3a8a"
    )
     self._active_transcript_tag = active_tag
     self._last_active_tag = active_tag

    # Only auto-scroll if user hasn't scrolled manually
     if not getattr(self, "_user_scrolled", False):
        self.timeline_box._textbox.see(f"{active_tag}.first")


   

    def _run_search_live(self):
     if getattr(self, "_search_running", False):
        return

     self._search_running = True
     try:
        query = self.search_var.get().strip()
        textbox = self.timeline_box._textbox

        # Clear previous highlights
        textbox.tag_remove("search_hit", "1.0", "end")

        self._search_matches = []
        self._search_index = -1

        if not query:
            return

        start_index = "1.0"

        while True:
            pos = textbox.search(query, start_index, stopindex="end", nocase=True)
            if not pos:
                break

            end_pos = f"{pos}+{len(query)}c"

            # Highlight ONLY matching word
            textbox.tag_add("search_hit", pos, end_pos)

            # Save for navigation
            self._search_matches.append((pos, end_pos))

            start_index = end_pos

        textbox.tag_configure(
            "search_hit",
            background="#7c2d12",
            foreground="white"
        )

        # Auto select first match (no audio)
        if self._search_matches:
            self._search_index = 0
            self._focus_search_result()

     finally:
        self._search_running = False




    # ⚠️ IMPORTANT: no auto-jump here 
    def _search_next(self):
     if not self._search_matches:
        return

     self._search_index = (self._search_index + 1) % len(self._search_matches)
     self._focus_search_result()


    def _search_prev(self):
     if not self._search_matches:
        return

     self._search_index = (self._search_index - 1) % len(self._search_matches)
     self._focus_search_result()


     
    def _highlight_current_word(self):

     if not hasattr(self, "_word_timeline"):
        return

     if not self._is_playing:
        return

     rate = self._playback_rate
     if not rate:
        return

     current_sec = self._playback_pos / rate

     active_word = None
     for start, end, tag in self._word_timeline:
        if start <= current_sec <= end:
            active_word = tag
            break

     if not active_word:
        return

     if getattr(self, "_last_active_word", None) == active_word:
        return

    # clear previous
     last = getattr(self, "_last_active_word", None)
     if last:
        try:
            self.timeline_box._textbox.tag_configure(last, background="")
        except:
            pass

     self.timeline_box._textbox.tag_configure(
        active_word,
        background="#2563eb",
        foreground="white"
    )

     self._last_active_word = active_word



     last = getattr(self, "_last_active_word", None)
     if last:
      self._clear_active_transcript_highlight()



     self.timeline_box._textbox.tag_configure(
        active_word,
        background="#2563eb",
        foreground="white"
    )

    def _set_playback_speed(self, speed: float):
     if self._playback_audio is None:
        return

     speed = float(speed)
     speed = max(0.25, min(speed, 4.0))

     if speed == getattr(self, "_playback_speed", 1.0):
        return

     self._playback_speed = float(speed)
     print(f"[Audio Player] Speed set to {speed}x")


    # ❌ DO NOT stop or restart stream here
    # Speed will apply smoothly in callback

     self._is_changing_speed = False 


        
    def _schedule_ui_update(self):
     if getattr(self, "_ui_update_scheduled", False):
        return

     self._ui_update_scheduled = True
     self.after(100, self._safe_ui_update)

     
     
    def _safe_ui_update(self):
    # Allow next scheduling
     self._ui_update_scheduled = False

    # Audio may not be ready
     if self._playback_audio is None or not self._is_playing:
        return

     try:
        self._update_seek_slider()
       # self._highlight_current_transcript()
       # self._highlight_current_word()
     except Exception as e:
        print("[UI Update Skipped]", e)
        
    def _reset_auto_scroll(self):
        self._user_scrolled = False  
       
    def _run_search(self):
     self._run_search_live()
     
    def _on_search_typing(self, event=None):
     if hasattr(self, "_search_after_id") and self._search_after_id:
        self.after_cancel(self._search_after_id)

     self._search_after_id = self.after(300, self._run_search_live)
     
     
    
    def _jump_to_search_result(self, play_audio: bool = False):
     if not self._search_matches:
        return

     if self._search_index < 0 or self._search_index >= len(self._search_matches):
        return

     start_sec, tag_name = self._search_matches[self._search_index]

     if not isinstance(tag_name, str):
        return

    # Clear previous highlight
     self._clear_active_transcript_highlight()

    # Highlight searched line
     self.timeline_box._textbox.tag_configure(
        tag_name,
        background="#1e3a8a"
    )
     self._active_transcript_tag = tag_name

    # Scroll only
     self.timeline_box._textbox.see(f"{tag_name}.first")

    
       
        
     



  
    def _load_audio_for_playback(self, explicit_meeting_dir: Optional[str] = None):
        # 1. Prefer the specific meeting passed in, otherwise fallback to dashboard
        meeting_dir = explicit_meeting_dir or getattr(self, "_dashboard_meeting_dir", None)

        print("DEBUG meeting_dir type:", type(meeting_dir))
        print("DEBUG meeting_dir value:", meeting_dir)

        if not isinstance(meeting_dir, str) or not meeting_dir:
            print("[Audio Player] No meeting directory")
            return

        audio_path = os.path.join(meeting_dir, "audio_raw.wav")
        if not os.path.exists(audio_path):
            print("[Audio Player] audio_raw.wav missing")
            return

        try:
            with wave.open(audio_path, "rb") as wf:
                rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())

            if rate <= 0:
                print("[Audio Player] Invalid sample rate")
                return

            audio_int16 = np.frombuffer(frames, dtype=np.int16)
            if channels > 1: audio_int16 = audio_int16.reshape(-1, channels)[:, 0]

            audio = audio_int16.astype(np.float32) / 32768.0
            audio = np.column_stack([audio, audio])

            self._playback_audio = audio
            self._playback_rate = rate
            self._audio_duration_sec = len(audio) / float(rate)
            self._playback_pos = 0
            self._last_playback_pos = 0

            print(f"[Audio Player] Audio loaded into memory from {os.path.basename(meeting_dir)}")

        except Exception as e:
            print("[Audio Player Load Error]", e)
            self._playback_audio = None
            self._playback_rate = None


     
    def _set_playback_state(self, state: str):
     self._playback_state = state

     is_busy = state in ("loading", "seeking")

     try:
        self.play_btn.configure(state="disabled" if is_busy else "normal")
        self.pause_btn.configure(state="disabled" if is_busy else "normal")
     except Exception:
        pass

    # Optional status indicator
     if hasattr(self, "status_pill"):
        if state == "loading":
            self.status_pill.configure(text="Loading audio…")
        elif state == "seeking":
            self.status_pill.configure(text="Seeking…")
        elif state == "playing":
            self.status_pill.configure(text="Playing")
        elif state == "paused":
            self.status_pill.configure(text="Paused")
        else:
            self.status_pill.configure(text="Idle")
            

    def add_bookmark(self):

     if self._playback_rate is None:
        return

     rate = float(self._playback_rate)
     if rate <= 0:
        return

    # ✅ Accurate second calculation
     if isinstance(rate, (int, float)) and rate > 0:
      current_sec = float(self._playback_pos) / rate
      current_sec = round(current_sec, 2)

      self._bookmarks.append(current_sec)

      print("[Bookmark] Saved at", current_sec, "seconds")

     self._render_bookmarks()


     
    def _clear_active_transcript_highlight(self):
     tag = self._active_transcript_tag
     if isinstance(tag, str):
        try:
            self.timeline_box._textbox.tag_configure(tag, background="")
        except Exception:
            pass
     self._active_transcript_tag = None

    def _on_transcript_single_click(self, tag_name: str):
     if not isinstance(tag_name, str):
        return

    # Clear previous highlight safely
     self._clear_active_transcript_highlight()

    # Highlight clicked line
     try:
        self.timeline_box._textbox.tag_configure(
            tag_name,
            background="#1e3a8a"
        )
     except Exception:
        return

     self._active_transcript_tag = tag_name

    # Scroll into view
     self.timeline_box._textbox.see(f"{tag_name}.first")
     
     
     
     
    def _focus_search_result(self):
     if not self._search_matches:
        return

     if self._search_index < 0 or self._search_index >= len(self._search_matches):
        return

     start, end = self._search_matches[self._search_index]

     textbox = self.timeline_box._textbox

    # Scroll to word
     textbox.see(start)

    # Optional: briefly flash active word
     textbox.tag_remove("search_active", "1.0", "end")
     textbox.tag_add("search_active", start, end)
     textbox.tag_configure(
        "search_active",
        background="#2563eb",
        foreground="white"
    )
 
   
    def _render_bookmarks(self):

     if not hasattr(self, "bookmark_box"):
        return

     textbox = self.bookmark_box._textbox  # internal tk Text

     textbox.configure(state="normal")
     textbox.delete("1.0", "end")

     if not getattr(self, "_bookmarks", None):
        textbox.insert("end", "No bookmarks yet.\n")
        textbox.configure(state="disabled")
        return

     for i, sec in enumerate(self._bookmarks):

        time_label = self._format_time(int(sec))
        tag = f"bookmark_{i}"

        start_index = textbox.index("end-1c")
        textbox.insert("end", f"{time_label}\n")
        end_index = textbox.index("end-1c")

        textbox.tag_add(tag, start_index, end_index)
        textbox.tag_configure(
            tag,
            foreground="#93c5fd",
            underline=True
        )

        # ✅ Single click → jump safely by index
        textbox.tag_bind(
            tag,
            "<Button-1>",
            lambda e, idx=i: self._jump_to_bookmark(idx)
        )

     textbox.configure(state="disabled")



    def _jump_to_bookmark(self, index: int):

     if not isinstance(index, int):
        return

     if index < 0 or index >= len(self._bookmarks):
        return

     sec = float(self._bookmarks[index])

     print("[Bookmark] Jumping to", round(sec, 3))

    # 🔒 Clear resume interference
     self._last_playback_pos = 0
     self._pending_seek_pos = None

    # 🔥 Route EVERYTHING through unified seek
     self._play_audio_from_elapsed(sec)



     
    def _on_seek_change(self, value):

     if self._playback_rate is None:
        return

     try:
        sec = float(value)
        rate = float(self._playback_rate)

        self._pending_seek_pos = int(sec * rate)

     except:
        pass

    def _on_seek_commit(self, event=None):

     if self._pending_seek_pos is None:
        return

    # Apply seek
     self._playback_pos = int(self._pending_seek_pos)
     self._pending_seek_pos = None

     rate = self._playback_rate
     if isinstance(rate, (int, float)) and rate > 0:
      current_sec = self._playback_pos / rate
      print("[Seek] Jumped to", round(current_sec, 2))


    # Restart playback cleanly
     self._stop_audio_stream()
     self.after(0, self._audio_play)
    
      
    def _build_final_index(self, meeting_dir: str):
     import os
     import json
     import numpy as np
     from rag.slide_extractor import SlideExtractor
     from rag.embedding_provider import LocalEmbeddingProvider
     from rag.vector_store import FaissVectorStore
     from merge_engine import MergeEngine

     if not isinstance(meeting_dir, str) or not meeting_dir or not os.path.exists(meeting_dir):
        print(f"[Indexing] ❌ Invalid or non-existent meeting_dir: {meeting_dir}")
        return

     print("\n[Indexing] STARTED")

     try:
        # 1. Load Transcript Chunks
        transcript_path = os.path.join(meeting_dir, "transcript_refined.json")
        if not os.path.exists(transcript_path):
            print("[Indexing] ❌ No transcript found at:", transcript_path)
            return

        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_chunks = json.load(f)

        # 2. Extract Slide Chunks
        print("[Indexing] Extracting slides...")
        extractor = SlideExtractor(meeting_dir)
        slide_chunks = extractor.extract()
        print(f"[Indexing] Slide chunks found: {len(slide_chunks)}")

        # 3. Merge Engines (Combine Text + Slides)
        print("[Indexing] Merging sources...")
        merger = MergeEngine(meeting_dir)
        all_chunks = merger.merge(transcript_chunks, slide_chunks)
        
        if not all_chunks:
            print("[Indexing] ❌ No chunks to index.")
            return

        # 4. Save the merged JSON (for metadata lookup)
        meta_path = os.path.join(meeting_dir, "chunks_final.json") 
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2)
        print(f"[Indexing] Metadata saved: {len(all_chunks)} total chunks")

        # 5. Create Embeddings
        print("[Indexing] Generating embeddings (this may take a moment)...")
        embedder = LocalEmbeddingProvider()
        
        # We index the "text" field from our merged chunks
        texts = [c.get("text", "") for c in all_chunks]
        embeddings = embedder.embed_texts(texts)
        embeddings = np.asarray(embeddings, dtype="float32")

        # 6. Build and Save FAISS Index
        index_path = os.path.join(meeting_dir, "vector_final.index")
        dimension = embeddings.shape[1]
        
        store = FaissVectorStore(dimension, index_path)
        store.build(embeddings)

        print(f"[Indexing] ✅ SUCCESS: Index built at {index_path}")

     except Exception as e:
        print(f"[Indexing] ❌ CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()
     
    def _update_answer_box(self, text: str):
    # Failsafe: check if the widget exists before trying to update it
     if not hasattr(self, "system_status_box"):
        return
        
    # 1. Temporarily enable the text box so we can modify it
     self.system_status_box.configure(state="normal")
    
    # 2. Clear any existing text from the first line ("1.0") to the end
     self.system_status_box.delete("1.0", "end")
    
    # 3. Insert the new text
     self.system_status_box.insert("end", text)
    
    # 4. Disable it again so the user can't type in it
     self.system_status_box.configure(state="disabled")
    def open_summary_window(self):
     from rag.summary_engine import SummaryEngine
   

     window = ctk.CTkToplevel(self)
     window.title("Meeting Summary")
     window.geometry("900x600")
     window.grab_set()
 
     meetings = [
        name for name in os.listdir("data")
        if os.path.isdir(os.path.join("data", name))
    ]

     selected_meeting = ctk.StringVar(value=meetings[0] if meetings else "")

     dropdown = ctk.CTkOptionMenu(
        window,
        values=meetings,
        variable=selected_meeting
    )
     dropdown.pack(pady=15)

    # -------------------------
    # SUMMARY TYPE SELECTOR
    # -------------------------
     summary_types = ["Quick Summary", "Executive Summary", "Detailed Breakdown"]
     selected_type = ctk.StringVar(value=summary_types[0])

     type_dropdown = ctk.CTkOptionMenu(
        window,
        values=summary_types,
        variable=selected_type
    )
     type_dropdown.pack(pady=10)

     summary_box = ctk.CTkTextbox(
        window,
        wrap="word",
        font=("Segoe UI", 14)
    )
     summary_box.pack(fill="both", expand=True, padx=20, pady=10)

     def generate_summary():

        meeting_name = selected_meeting.get()
        meeting_dir = os.path.join("data", meeting_name)
        mode = selected_type.get()

        summary_box.delete("1.0", "end")
        summary_box.insert("end", "Generating summary...\n")

        engine = SummaryEngine()

        def run():
            summary = engine.summarize_meeting(meeting_dir, mode)

            def update():
                summary_box.delete("1.0", "end")
                summary_box.insert("end", summary)

            self.after(0, update)

        threading.Thread(target=run, daemon=True).start()

     button = ctk.CTkButton(
        window,
        text="Generate Summary",
        command=generate_summary
    )
     button.pack(pady=10)
    def _gather_global_stats(self):
        import os
        import json
        import wave
        
        base_dir = "data"
        stats = {
            "total_classes": 0,
            "total_slides": 0,
            "total_words": 0,
            "total_audio_seconds": 0.0
        }
        
        if not os.path.exists(base_dir): 
            return stats

        for folder in os.listdir(base_dir):
            folder_path = os.path.join(base_dir, folder)
            if not os.path.isdir(folder_path): continue

            stats["total_classes"] += 1

            # Count Slides
            slides_dir = os.path.join(folder_path, "slides")
            if os.path.exists(slides_dir):
                stats["total_slides"] += len([f for f in os.listdir(slides_dir) if f.lower().endswith(('.jpg', '.png'))])

            # Count Words in Transcript
            transcript_path = os.path.join(folder_path, "transcript_refined.json")
            if os.path.exists(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for entry in data:
                            stats["total_words"] += len(entry.get("text", "").split())
                except: 
                    pass

            # Calculate Exact Audio Duration
            audio_path = os.path.join(folder_path, "audio_raw.wav")
            if os.path.exists(audio_path):
                try:
                    with wave.open(audio_path, "rb") as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        stats["total_audio_seconds"] += frames / float(rate)
                except: 
                    pass

        return stats
    def _refresh_mini_stats(self):
        """Silently updates the sidebar mini-dashboard every 10 seconds."""
        try:
            stats = self._gather_global_stats()
            hrs = int(stats['total_audio_seconds'] // 3600)
            mins = int((stats['total_audio_seconds'] % 3600) // 60)
            time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

            self.lbl_mini_classes.configure(text=f"📚 Classes: {stats['total_classes']}")
            self.lbl_mini_words.configure(text=f"📝 Words: {stats['total_words']:,}")
            self.lbl_mini_audio.configure(text=f"🎙️ Audio: {time_str}")
        except Exception:
            pass
        # Re-run this check every 10 seconds
        self.after(10000, self._refresh_mini_stats)
    def open_global_dashboard(self):
        # 1. Fetch the data cruncher
        stats = self._gather_global_stats()
        
        # Format the audio time beautifully
        hrs = int(stats['total_audio_seconds'] // 3600)
        mins = int((stats['total_audio_seconds'] % 3600) // 60)
        time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

        # 2. Setup the Window
        window = ctk.CTkToplevel(self)
        window.title("OS Command Center")
        window.geometry("900x550")
        window.configure(fg_color=self.BG)
        window.grab_set()
        window.focus_force()

        # 3. Header
        header = ctk.CTkFrame(window, fg_color=self.BG)
        header.pack(fill="x", padx=40, pady=(40, 20))
        
        ctk.CTkLabel(header, text="📊 OS Command Center", font=ctk.CTkFont(family=self.FONT_FAMILY, size=28, weight="bold"), text_color=self.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="Your academic life, quantified.", font=ctk.CTkFont(family=self.FONT_FAMILY, size=15), text_color=self.TEXT_SECONDARY).pack(side="left", padx=(15, 0), pady=(8,0))

        # 4. The Grid System
        grid_top = ctk.CTkFrame(window, fg_color=self.BG)
        grid_top.pack(fill="both", expand=True, padx=30, pady=10)
        
        grid_bottom = ctk.CTkFrame(window, fg_color=self.BG)
        grid_bottom.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        # Reusable Card Builder
        def make_stat_card(parent, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=self.CARD, corner_radius=self.RADIUS_CARD, border_color=self.BORDER, border_width=1)
            card.pack(side="left", fill="both", expand=True, padx=10)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=self.FONT_FAMILY, size=15, weight="bold"), text_color=self.TEXT_SECONDARY).pack(pady=(35, 5))
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(family=self.FONT_FAMILY, size=42, weight="bold"), text_color=color).pack(pady=(0, 35))

        # Render the Metric Cards!
        make_stat_card(grid_top, "Total Classes", stats["total_classes"], self.ACCENT)
        make_stat_card(grid_top, "Recorded Audio", time_str, self.SUCCESS)
        
        # The {:,} adds commas to big numbers (e.g., 10,450 instead of 10450)
        make_stat_card(grid_bottom, "Words Transcribed", f"{stats['total_words']:,}", "#facc15") # Vibrant Yellow
        make_stat_card(grid_bottom, "Slides Captured", f"{stats['total_slides']:,}", "#60a5fa") # Crisp Blue 
    def open_revision_workspace(self):
        from rag.ask_engine import AskEngine
        from rag.summary_engine import SummaryEngine
        import os
        import threading
        import re

        window = ctk.CTkToplevel(self)
        window.title("Revision Workspace")
        window.geometry("1100x750")
        window.configure(fg_color=self.BG)
        window.grab_set()
        
        # 💡 PRO TIP: If you want to hide the default Windows/macOS title bar 
        # completely to make it look like a pure SaaS overlay, un-comment the line below!
        # window.overrideredirect(True)

        # 🔥 NEW: Dashboard-Style Custom Close Button
        close_x = ctk.CTkButton(
            window,
            text="✕",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=self.BORDER,
            hover_color=self.DANGER,
            text_color=self.TEXT_PRIMARY,
            font=ctk.CTkFont(size=16, weight="bold"),
            cursor="hand2",
            command=window.destroy
        )
        # Pin it to the absolute top-right corner
        close_x.place(relx=1.0, x=-30, y=25, anchor="ne")
        

        # ================= HEADER =================
        

        # ================= HEADER =================
        header = ctk.CTkFrame(window, fg_color=self.BG)
        header.pack(fill="x", padx=40, pady=(30, 10))

        title = ctk.CTkLabel(
            header,
            text="Revision Workspace",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        title.pack(side="left")

        # Meetings list
        meetings = ["All Classes"] + [
            name for name in os.listdir("data")
            if os.path.isdir(os.path.join("data", name))
        ]

        selected_class = ctk.StringVar(value="All Classes")

        dropdown = ctk.CTkOptionMenu(
            header,
            values=meetings,
            variable=selected_class,
            width=200
        )
        dropdown.pack(side="left", padx=(20, 0))
        toolbar = ctk.CTkFrame(window, fg_color="transparent")
        toolbar.pack(fill="x", padx=40, pady=(0, 10))

        # ================= SUMMARIZE BUTTON =================
        def summarize():
            selected = selected_class.get()

            if selected == "All Classes":
                answer_box.configure(state="normal")
                answer_box.delete("1.0", "end")
                answer_box.insert("end", "⚠ Please select a specific class to summarize.")
                answer_box.configure(state="disabled")
                return

            meeting_dir = os.path.join("data", selected)

            answer_box.configure(state="normal")
            answer_box.delete("1.0", "end")
            answer_box.insert("end", "Generating summary...\n")
            answer_box.configure(state="disabled")

            engine = SummaryEngine()

            def run():
                summary = engine.summarize_meeting(meeting_dir, "Executive Summary")
                def update():
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    answer_box.insert("end", summary)
                    answer_box.configure(state="disabled")
                self.after(0, update)

            threading.Thread(target=run, daemon=True).start()

        summary_btn = ctk.CTkButton(
            toolbar,
            text="📚 Summarize",
            width=140,
            height=40,
            corner_radius=10,
            fg_color=self.ACCENT,
            hover_color="#4338ca",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=summarize
        )
        summary_btn.pack(side="right")
    # ================= FLASHCARD BUTTON & LOGIC =================
        def open_flashcard_ui(cards):
            fc_window = ctk.CTkToplevel(window)
            fc_window.title("Auto-Anki Flashcards")
            fc_window.geometry("700x500")
            fc_window.configure(fg_color=self.BG)
            fc_window.grab_set()
            fc_window.focus_force()

            state = {"index": 0, "flipped": False}

            # Top counter
            counter_label = ctk.CTkLabel(fc_window, text=f"Card 1 of {len(cards)}", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"), text_color=self.TEXT_SECONDARY)
            counter_label.pack(pady=(30, 10))

            # The Card itself
            card_frame = ctk.CTkFrame(fc_window, fg_color=self.CARD, corner_radius=20, border_color=self.BORDER, border_width=2)
            card_frame.pack(fill="both", expand=True, padx=60, pady=20)
            card_frame.pack_propagate(False)

            card_type_label = ctk.CTkLabel(card_frame, text="QUESTION", font=ctk.CTkFont(family=self.FONT_FAMILY, size=12, weight="bold"), text_color=self.ACCENT)
            card_type_label.pack(pady=(20, 0))

            content_label = ctk.CTkLabel(card_frame, text="", font=ctk.CTkFont(family=self.FONT_FAMILY, size=22), text_color=self.TEXT_PRIMARY, wraplength=500, justify="center")
            content_label.pack(expand=True, padx=20)

            def update_card_ui():
                card = cards[state["index"]]
                counter_label.configure(text=f"Card {state['index'] + 1} of {len(cards)}")
                
                if state["flipped"]:
                    card_type_label.configure(text="ANSWER", text_color=self.SUCCESS)
                    content_label.configure(text=card.get("answer", ""))
                    card_frame.configure(border_color=self.SUCCESS)
                else:
                    card_type_label.configure(text="QUESTION", text_color=self.ACCENT)
                    content_label.configure(text=card.get("question", ""))
                    card_frame.configure(border_color=self.BORDER)

            def flip_card():
                state["flipped"] = not state["flipped"]
                update_card_ui()

            def next_card():
                if state["index"] < len(cards) - 1:
                    state["index"] += 1
                    state["flipped"] = False
                    update_card_ui()

            def prev_card():
                if state["index"] > 0:
                    state["index"] -= 1
                    state["flipped"] = False
                    update_card_ui()

            # Controls
            controls = ctk.CTkFrame(fc_window, fg_color=self.BG)
            controls.pack(fill="x", padx=60, pady=(0, 40))

            ctk.CTkButton(controls, text="◀ Prev", width=100, height=40, corner_radius=self.RADIUS_BTN, fg_color="#1f2937", hover_color="#374151", cursor="hand2", command=prev_card).pack(side="left")
            ctk.CTkButton(controls, text="🔄 Flip Card", height=48, corner_radius=self.RADIUS_BTN, fg_color=self.ACCENT, hover_color="#4338ca", font=ctk.CTkFont(family=self.FONT_FAMILY, size=15, weight="bold"), cursor="hand2", command=flip_card).pack(side="left", expand=True, padx=10)
            ctk.CTkButton(controls, text="Next ▶", width=100, height=40, corner_radius=self.RADIUS_BTN, fg_color="#1f2937", hover_color="#374151", cursor="hand2", command=next_card).pack(side="right")
        # ... [Your existing Next/Prev Controls frame is here] ...
            # ctk.CTkButton(controls, text="Next ▶", ...).pack(side="right")

            # ================= 📦 ANKI EXPORT LOGIC =================
            def export_deck():
                export_btn.configure(text="⏳ Packaging...", state="disabled")
                
                def run_export():
                    try:
                        from rag.anki_exporter import AnkiExporter
                        import threading
                        
                        exporter = AnkiExporter()
                        deck_name = f"AI Deck - {selected_class.get()}"
                        
                        # Generate the .apkg file
                        filepath = exporter.export_to_apkg(deck_name, cards)
                        
                        # Show beautiful toast and update button
                        self.after(0, lambda: self.show_toast(f"Deck exported to /exports folder!", type="success"))
                        self.after(0, lambda: export_btn.configure(text="✅ Exported Successfully", text_color=self.SUCCESS))
                    except Exception as e:
                        print(f"[Anki Export Error] {e}")
                        self.after(0, lambda: self.show_toast("Export failed. Check terminal.", type="error"))
                        self.after(0, lambda: export_btn.configure(text="📦 Export to Anki (.apkg)", state="normal"))

                import threading
                threading.Thread(target=run_export, daemon=True).start()

            export_btn = ctk.CTkButton(
                fc_window, 
                text="📦 Export to Anki (.apkg)", 
                height=35,
                corner_radius=self.RADIUS_BTN,
                fg_color="transparent",
                hover_color="#1f2937",
                border_color=self.BORDER,
                border_width=1,
                font=ctk.CTkFont(family=self.FONT_FAMILY, size=13, weight="bold"),
                cursor="hand2",
                command=export_deck
            )
            export_btn.pack(pady=(10, 20))

            update_card_ui() # <--- This should be the last line of the UI function
         
        def generate_flashcards_trigger():
            selected = selected_class.get()
            if selected == "All Classes":
                answer_box.configure(state="normal")
                answer_box.delete("1.0", "end")
                answer_box.insert("end", "⚠ Please select a specific class to generate flashcards.")
                answer_box.configure(state="disabled")
                return

            meeting_map, _ = self._get_formatted_meetings()
            meeting_folder = meeting_map.get(selected, selected)
            meeting_dir = os.path.join("data", meeting_folder)

            # 🔥 Disable button and start progress bar
            flashcard_btn.configure(state="disabled")
            progress_bar.pack(fill="x", pady=(0, 10))
            progress_bar.configure(mode="indeterminate")
            progress_bar.start()

            answer_box.configure(state="normal")
            answer_box.delete("1.0", "end")
            answer_box.insert("end", f"🧠 Reading transcript and generating AI flashcards...\n")
            answer_box.configure(state="disabled")

            def run():
                from rag.flashcard_engine import FlashcardEngine
                engine = FlashcardEngine()
                cards = engine.generate_flashcards(meeting_dir)
                
                # 🔥 Stop progress bar and re-enable button
                def cleanup():
                    progress_bar.stop()
                    progress_bar.pack_forget()
                    flashcard_btn.configure(state="normal")
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    answer_box.insert("end", "✅ Flashcards generated! Opening deck...")
                    answer_box.configure(state="disabled")
                    open_flashcard_ui(cards)

                self.after(0, cleanup)

            threading.Thread(target=run, daemon=True).start()

        flashcard_btn = ctk.CTkButton(
            toolbar,
            text="🧠 Flashcards",
            width=140,
            height=40,
            corner_radius=self.RADIUS_BTN,
            fg_color="#1f2937", # Darker button so it doesn't clash with Summarize
            hover_color="#374151",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=generate_flashcards_trigger
        )
        flashcard_btn.pack(side="right", padx=(0, 10))
        
    # ================= QUIZ BUTTON & LOGIC =================
        def open_quiz_ui(quiz_data):
            quiz_window = ctk.CTkToplevel(window)
            quiz_window.title("Auto-Quiz")
            quiz_window.geometry("800x650")
            quiz_window.configure(fg_color=self.BG)
            quiz_window.grab_set()
            quiz_window.focus_force()

            state = {
                "index": 0, 
                "score": 0,
                "answered_current": False # Prevents changing answer after clicking
            }

            # Top Header (Score & Progress)
            header_frame = ctk.CTkFrame(quiz_window, fg_color=self.BG)
            header_frame.pack(fill="x", padx=40, pady=(30, 10))

            progress_label = ctk.CTkLabel(header_frame, text=f"Question 1 of {len(quiz_data)}", font=ctk.CTkFont(family=self.FONT_FAMILY, size=16, weight="bold"), text_color=self.TEXT_SECONDARY)
            progress_label.pack(side="left")

            score_label = ctk.CTkLabel(header_frame, text="Score: 0", font=ctk.CTkFont(family=self.FONT_FAMILY, size=16, weight="bold"), text_color=self.ACCENT)
            score_label.pack(side="right")

            # Main Question Area
            q_frame = ctk.CTkFrame(quiz_window, fg_color=self.CARD, corner_radius=self.RADIUS_CARD, border_color=self.BORDER, border_width=1)
            q_frame.pack(fill="both", expand=True, padx=40, pady=(10, 20))

            question_label = ctk.CTkLabel(q_frame, text="", font=ctk.CTkFont(family=self.FONT_FAMILY, size=20, weight="bold"), text_color=self.TEXT_PRIMARY, wraplength=650, justify="left")
            question_label.pack(anchor="nw", padx=30, pady=(30, 20))

            # Options Container
            options_frame = ctk.CTkFrame(q_frame, fg_color="transparent")
            options_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
            
            option_buttons = [] # Store references to the buttons so we can update their colors

            # Explanation Area (Hidden initially)
            explanation_box = ctk.CTkTextbox(q_frame, height=80, fg_color="#0b1220", text_color=self.TEXT_SECONDARY, font=ctk.CTkFont(family=self.FONT_FAMILY, size=13), wrap="word", border_width=1, border_color=self.BORDER, corner_radius=self.RADIUS_BTN)
            
            # Bottom Controls
            controls_frame = ctk.CTkFrame(quiz_window, fg_color=self.BG)
            controls_frame.pack(fill="x", padx=40, pady=(0, 30))

            next_btn = ctk.CTkButton(controls_frame, text="Next Question ▶", height=40, corner_radius=self.RADIUS_BTN, fg_color=self.ACCENT, hover_color="#4338ca", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"), cursor="hand2", state="disabled")
            next_btn.pack(side="right")

            def handle_answer_click(selected_option_idx, correct_answer_text):
                if state["answered_current"]: return # Already answered
                state["answered_current"] = True
                
                selected_btn = option_buttons[selected_option_idx]
                selected_text = selected_btn.cget("text")
                
                # Check if correct
                is_correct = selected_text.strip().lower() == correct_answer_text.strip().lower()

                # Highlight the clicked button
                if is_correct:
                    selected_btn.configure(fg_color=self.SUCCESS, border_color=self.SUCCESS)
                    state["score"] += 1
                    score_label.configure(text=f"Score: {state['score']}")
                else:
                    selected_btn.configure(fg_color=self.DANGER, border_color=self.DANGER)
                    # Highlight the actual correct answer in green
                    for btn in option_buttons:
                        if btn.cget("text").strip().lower() == correct_answer_text.strip().lower():
                            btn.configure(fg_color="#064e3b", border_color=self.SUCCESS, border_width=2) # Dark green background

                # Show Explanation
                explanation_box.pack(fill="x", padx=30, pady=(10, 20))
                explanation_box.configure(state="normal")
                explanation_box.delete("1.0", "end")
                explanation_prefix = "✅ Correct! " if is_correct else "❌ Incorrect. "
                explanation_box.insert("end", explanation_prefix + quiz_data[state["index"]].get("explanation", ""))
                explanation_box.configure(state="disabled")

                # Enable Next Button
                if state["index"] == len(quiz_data) - 1:
                    next_btn.configure(text="Finish Quiz", state="normal")
                else:
                    next_btn.configure(state="normal")

            def load_question(index):
                q_data = quiz_data[index]
                state["answered_current"] = False
                
                progress_label.configure(text=f"Question {index + 1} of {len(quiz_data)}")
                question_label.configure(text=q_data.get("question", ""))
                
                # Clear previous options
                for widget in options_frame.winfo_children():
                    widget.destroy()
                option_buttons.clear()

                # Hide explanation
                explanation_box.pack_forget()
                next_btn.configure(state="disabled")

                correct_ans = q_data.get("answer", "")
                
                # Render Option Buttons
                for i, opt_text in enumerate(q_data.get("options", [])):
                    btn = ctk.CTkButton(
                        options_frame,
                        text=opt_text,
                        height=45,
                        corner_radius=self.RADIUS_BTN,
                        fg_color="#1f2937",
                        hover_color="#374151",
                        text_color=self.TEXT_PRIMARY,
                        font=ctk.CTkFont(family=self.FONT_FAMILY, size=14),
                        anchor="w", # Left align text
                        border_width=1,
                        border_color=self.BORDER,
                        cursor="hand2"
                    )
                    btn.pack(fill="x", pady=(0, 10))
                    # Bind click (pass current index and correct answer)
                    btn.configure(command=lambda idx=i, ans=correct_ans: handle_answer_click(idx, ans))
                    option_buttons.append(btn)

            def go_next():
                if state["index"] < len(quiz_data) - 1:
                    state["index"] += 1
                    load_question(state["index"])
                else:
                    # Finished
                    for widget in q_frame.winfo_children():
                        widget.destroy()
                    next_btn.pack_forget()
                    
                    progress_label.configure(text="Quiz Complete!")
                    final_score_label = ctk.CTkLabel(q_frame, text=f"Final Score: {state['score']} / {len(quiz_data)}", font=ctk.CTkFont(family=self.FONT_FAMILY, size=32, weight="bold"), text_color=self.ACCENT)
                    final_score_label.pack(expand=True)
                    
                    close_btn = ctk.CTkButton(q_frame, text="Close", width=140, height=48, corner_radius=self.RADIUS_BTN, fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=self.FONT_FAMILY, size=15, weight="bold"), cursor="hand2", command=quiz_window.destroy)
                    close_btn.pack(pady=30)

            next_btn.configure(command=go_next)
            load_question(0) # Init first question

        def generate_quiz_trigger():
            selected = selected_class.get()
            if selected == "All Classes":
                answer_box.configure(state="normal")
                answer_box.delete("1.0", "end")
                answer_box.insert("end", "⚠ Please select a specific class to generate a quiz.")
                answer_box.configure(state="disabled")
                return

            meeting_map, _ = self._get_formatted_meetings()
            meeting_folder = meeting_map.get(selected, selected)
            meeting_dir = os.path.join("data", meeting_folder)

            # 🔥 Disable button and start progress bar
            quiz_btn.configure(state="disabled")
            progress_bar.pack(fill="x", pady=(0, 10))
            progress_bar.configure(mode="indeterminate")
            progress_bar.start()

            answer_box.configure(state="normal")
            answer_box.delete("1.0", "end")
            answer_box.insert("end", f"📝 Reading transcript and writing AI quiz...\n")
            answer_box.configure(state="disabled")

            def run():
                from rag.quiz_engine import QuizEngine
                engine = QuizEngine()
                quiz_data = engine.generate_quiz(meeting_dir)
                
                # 🔥 Stop progress bar and re-enable button
                def cleanup():
                    progress_bar.stop()
                    progress_bar.pack_forget()
                    quiz_btn.configure(state="normal")
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    answer_box.insert("end", "✅ Quiz generated! Good luck...")
                    answer_box.configure(state="disabled")
                    open_quiz_ui(quiz_data)

                self.after(0, cleanup)

            threading.Thread(target=run, daemon=True).start()

        quiz_btn = ctk.CTkButton(
            toolbar,
            text="📝 Take Quiz",
            width=140,
            height=40,
            corner_radius=self.RADIUS_BTN,
            fg_color="#1f2937", 
            hover_color="#374151",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=generate_quiz_trigger
        )
        quiz_btn.pack(side="right") 
    # ================= SYLLABUS BUTTON & LOGIC =================
        def open_syllabus_ui(concepts):
            syl_window = ctk.CTkToplevel(window)
            syl_window.title("Auto-Generated Syllabus")
            syl_window.geometry("800x650")
            syl_window.configure(fg_color=self.BG)
            syl_window.grab_set()
            
            # Header
            header_frame = ctk.CTkFrame(syl_window, fg_color=self.BG)
            header_frame.pack(fill="x", padx=40, pady=(30, 10))
            ctk.CTkLabel(header_frame, text="📖 Class Syllabus", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.TEXT_PRIMARY).pack(side="left")
            
            # Scrollable List
            list_frame = ctk.CTkScrollableFrame(syl_window, fg_color=self.BG)
            list_frame.pack(fill="both", expand=True, padx=40, pady=(10, 30))
            
            for i, concept in enumerate(concepts):
                card = ctk.CTkFrame(list_frame, fg_color=self.CARD, corner_radius=12, border_color=self.BORDER, border_width=1)
                card.pack(fill="x", pady=(0, 15))
                
                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=20, pady=(20, 5))
                
                title = concept.get("title", "Unknown Concept")
                importance = str(concept.get("importance", "Medium")).strip()
                
                # Color code the importance tags
                color = self.DANGER if "high" in importance.lower() else self.SUCCESS if "low" in importance.lower() else self.ACCENT
                
                ctk.CTkLabel(top_row, text=f"{i+1}. {title}", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.TEXT_PRIMARY).pack(side="left")
                ctk.CTkLabel(top_row, text=importance.upper(), font=ctk.CTkFont(size=12, weight="bold"), text_color=color, fg_color="#1f2937", corner_radius=4, padx=8, pady=4).pack(side="right")
                
                explanation = concept.get("explanation", "No explanation provided.")
                ctk.CTkLabel(card, text=explanation, font=ctk.CTkFont(size=14), text_color=self.TEXT_SECONDARY, wraplength=650, justify="left").pack(anchor="w", padx=20, pady=(0, 20))

        def generate_syllabus_trigger():
            selected = selected_class.get()
            if selected == "All Classes":
                answer_box.configure(state="normal")
                answer_box.delete("1.0", "end")
                answer_box.insert("end", "⚠ Please select a specific class to generate a syllabus.")
                answer_box.configure(state="disabled")
                return

            meeting_map, _ = self._get_formatted_meetings()
            meeting_folder = meeting_map.get(selected, selected)
            meeting_dir = os.path.join("data", meeting_folder)

            # Disable button and start progress bar
            syl_btn.configure(state="disabled")
            progress_bar.pack(fill="x", pady=(0, 10))
            progress_bar.configure(mode="indeterminate")
            progress_bar.start()

            answer_box.configure(state="normal")
            answer_box.delete("1.0", "end")
            answer_box.insert("end", f"📖 Analyzing transcript to extract core concepts...\n")
            answer_box.configure(state="disabled")

            def run():
                from rag.concept_engine import ConceptEngine
                engine = ConceptEngine()
                concepts = engine.extract_syllabus(meeting_dir)
                
                def cleanup():
                    progress_bar.stop()
                    progress_bar.pack_forget()
                    syl_btn.configure(state="normal")
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    answer_box.insert("end", "✅ Syllabus generated! Opening viewer...")
                    answer_box.configure(state="disabled")
                    open_syllabus_ui(concepts)

                self.after(0, cleanup)

            import threading
            threading.Thread(target=run, daemon=True).start()

        syl_btn = ctk.CTkButton(
            toolbar,
            text="📖 Syllabus",
            width=140,
            height=40,
            corner_radius=self.RADIUS_BTN,
            fg_color="#1f2937", 
            hover_color="#374151",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=generate_syllabus_trigger
        )
        syl_btn.pack(side="right", padx=(0, 10)) 
    # ================= EXAM PREDICTOR BUTTON & LOGIC =================
        def open_exam_ui(predictions):
            ex_window = ctk.CTkToplevel(window)
            ex_window.title("AI Exam Predictor")
            ex_window.geometry("850x700")
            ex_window.configure(fg_color=self.BG)
            ex_window.grab_set()

            ctk.CTkLabel(ex_window, text="🎯 Exam Probability Heatmap", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 20))
            
            scroll = ctk.CTkScrollableFrame(ex_window, fg_color=self.BG)
            scroll.pack(fill="both", expand=True, padx=40, pady=(0, 30))

            for p in predictions:
                prob_color = "#ef4444" if p.get("probability") == "High" else "#facc15"
                
                card = ctk.CTkFrame(scroll, fg_color=self.CARD, corner_radius=12, border_color=prob_color, border_width=1)
                card.pack(fill="x", pady=10)

                ctk.CTkLabel(card, text=p.get("topic", "Unknown"), font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
                
                reason = ctk.CTkLabel(card, text=f"Reasoning: {p.get('reasoning')}", font=ctk.CTkFont(size=13, slant="italic"), text_color=self.TEXT_SECONDARY, wraplength=700, justify="left")
                reason.pack(anchor="w", padx=20, pady=5)

                q_box = ctk.CTkFrame(card, fg_color="#1e2937", corner_radius=8)
                q_box.pack(fill="x", padx=20, pady=(5, 15))
                ctk.CTkLabel(q_box, text=f"Potential Question: {p.get('predicted_question')}", font=ctk.CTkFont(size=14), wraplength=650).pack(padx=15, pady=10)

        def generate_exam_trigger():
            selected = selected_class.get()
            if selected == "All Classes":
                return
            
            meeting_map, _ = self._get_formatted_meetings()
            meeting_dir = os.path.join("data", meeting_map.get(selected, selected))

            exam_btn.configure(state="disabled")
            progress_bar.pack(fill="x", pady=(0, 10))
            progress_bar.start()

            def run():
                from rag.exam_engine import ExamPredictor
                engine = ExamPredictor()
                predictions = engine.predict_exam_topics(meeting_dir)
                
                def cleanup():
                    progress_bar.stop()
                    progress_bar.pack_forget()
                    exam_btn.configure(state="normal")
                    open_exam_ui(predictions)
                self.after(0, cleanup)

            threading.Thread(target=run, daemon=True).start()

        exam_btn = ctk.CTkButton(
            toolbar,
            text="🎯 Predict Exam",
            width=140,
            height=40,
            corner_radius=self.RADIUS_BTN,
            fg_color="#312e81", # Deep indigo
            hover_color="#3730a3",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=generate_exam_trigger
        )
        exam_btn.pack(side="right", padx=(0, 10))          
        # ================= 1. FOOTER CONTAINER (Glued to Bottom) =================
        # 🔥 Pack this FIRST so it reserves space at the bottom of the window!
        footer_frame = ctk.CTkFrame(window, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=40, pady=(0, 30))

        # ================= 2. ANSWER AREA (Fills all middle space) =================
        # 🔥 Wrap in a container and pack it SECOND so it fills the remaining gap safely
        answer_container = ctk.CTkFrame(window, fg_color="transparent")
        answer_container.pack(side="top", fill="both", expand=True, padx=40, pady=(0, 20))

        answer_box = ctk.CTkTextbox(
            answer_container,
            fg_color="transparent",
            text_color="#ffffff",
            font=("Inter", 15),
            wrap="word"
        )
        # expand=True forces it to eat all remaining vertical space safely!
        answer_box.pack(side="top", fill="both", expand=True)

        # Apply Markdown Tag Configs
        answer_box.tag_config("class_tag", foreground="#60a5fa", underline=True)
        answer_box.tag_config("slide_tag", foreground="#fbbf24", underline=True)
        answer_box.tag_config("timestamp_tag", foreground="#34d399", underline=True)
        # 🔥 FIX: Bypass CustomTkinter's lock by targeting the internal raw text widget
        answer_box._textbox.tag_config("bold_tag", font=(self.FONT_FAMILY, 16, "bold"), foreground="#ffffff")
        answer_box._textbox.tag_config("code_tag", font=("Consolas", 14), foreground="#a78bfa", background="#1e1e2f")

        def open_timestamp_event(event):
            index = event.widget.index(f"@{event.x},{event.y}")
            word = event.widget.get(index + " wordstart", index + " wordend")
            match = re.match(r"\[(\d+):(\d+)\]", word)
            if match:
                mins = int(match.group(1))
                secs = int(match.group(2))
                total = mins * 60 + secs
                self._play_audio_from_elapsed(total)

        answer_box.tag_bind("timestamp_tag", "<Button-1>", open_timestamp_event)

        def open_slide_event(event):
            text_widget = event.widget
            click_index = text_widget.index(f"@{event.x},{event.y}")
            ranges = text_widget.tag_ranges("slide_tag")
            for i in range(0, len(ranges), 2):
                start = ranges[i]
                end = ranges[i+1]
                if text_widget.compare(start, "<=", click_index) and text_widget.compare(click_index, "<=", end):
                    full_slide_name = text_widget.get(start, end).strip()
                    print(f"[UI] Opening requested slide: {full_slide_name}")
                    self._open_slide(full_slide_name)
                    break
        
        answer_box.tag_bind("slide_tag", "<Button-1>", open_slide_event)

        # ================= RICH EMPTY STATE =================
        welcome_msg = (
            "✨ Welcome to the Revision Workspace ✨\n\n"
            "Your AI study OS is ready. What would you like to do?\n\n"
            "📚 Summarize: Get a quick, executive overview of the lecture.\n"
            "💬 Or simply type a question below to search the class memory! \n"
            "💡 Tip: Type '@' in the input box to ask questions across specific classes."
        )
        answer_box.insert("end", welcome_msg)
        answer_box.tag_config("center", justify="center")
        answer_box.tag_add("center", "1.0", "end")
        answer_box.configure(state="disabled")

        # ================= 3. POPULATE FOOTER ELEMENTS =================
        # 🔥 NEW: A permanent, invisible container to hold the progress bar safely
        progress_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
        progress_container.pack(side="top", fill="x")

        # 🔧 FIX: Progress bars require a solid color, not "transparent"
        progress_bar = ctk.CTkProgressBar(progress_container, height=4, fg_color=self.BG, progress_color=self.ACCENT)
        progress_bar.set(0)

        evidence_frame = ctk.CTkScrollableFrame(footer_frame, height=60, fg_color="transparent", orientation="horizontal")
        evidence_frame.pack(side="top", fill="x", pady=(0, 10))

        suggestion_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        suggestion_frame.pack(side="top", fill="x", pady=(0, 5))

        # 🔥 NEW: Sleek ChatGPT-Style Input Pill
        input_row = ctk.CTkFrame(footer_frame, fg_color="#1c192b", corner_radius=26, border_width=1, border_color=self.BORDER)
        input_row.pack(side="top", fill="x", ipady=4)

        # Subtle icon
        ctk.CTkLabel(input_row, text="✨", font=("Inter", 18)).pack(side="left", padx=(20, 5))

        question_entry = ctk.CTkEntry(
            input_row,
            height=48,
            fg_color="transparent",
            border_width=0, # Remove harsh borders inside the pill
            placeholder_text="Ask anything about the class...",
            placeholder_text_color=self.TEXT_SECONDARY,
            text_color=self.TEXT_PRIMARY,
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=15)
        )
        question_entry.pack(side="left", fill="x", expand=True, padx=5)

        def ask():
            q = question_entry.get().strip()
            if not q: return

            # Disable input so they don't spam the button
            ask_btn.configure(state="disabled")
            question_entry.configure(state="disabled")

            # Show and start the pulsing progress bar
            progress_bar.pack(fill="x", pady=(0, 10))
            progress_bar.configure(mode="indeterminate")
            progress_bar.start()

            answer_box.configure(state="normal")
            answer_box.delete("1.0", "end")
            answer_box.insert("end", "Analyzing transcript and slides...\n")
            answer_box.configure(state="disabled")

            engine = self.ask_engine or AskEngine(base_data_dir="data")
            self.ask_engine = engine

            def run():
                mentioned_classes = self._parse_class_mentions(q)
                clean_question = self._remove_class_tags(q)

                # 🔥 FIX: Force the AskEngine to respect the dropdown menu selection!
                dropdown_selection = selected_class.get()
                if dropdown_selection != "All Classes":
                    # Convert the pretty dropdown name back to the raw folder name
                    meeting_map, _ = self._get_formatted_meetings()
                    target_folder = meeting_map.get(dropdown_selection, dropdown_selection)
                    
                    # Add it to the search list if it isn't already there
                    if target_folder not in mentioned_classes:
                        mentioned_classes.append(target_folder)

                def clear_box():
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    answer_box.configure(state="disabled")
                self.after(0, clear_box)

                full_response = ""

                # Now, it will strictly search ONLY the classes in mentioned_classes
                if mentioned_classes:
                    stream_gen = engine.ask_stream(clean_question, selected_meetings=mentioned_classes)
                else:
                    stream_gen = engine.ask_stream(clean_question)

                first_token_received = False
                token_buffer = ""  # 🔥 NEW: Create a buffer to batch tokens

                for token in stream_gen:
                    if token:  
                        # Stop the progress bar the moment the AI starts talking!
                        if not first_token_received:
                            first_token_received = True
                            def stop_loader():
                                progress_bar.stop()
                                progress_bar.pack_forget()
                                ask_btn.configure(state="normal")
                                question_entry.configure(state="normal")
                                question_entry.delete(0, "end")
                            self.after(0, stop_loader)

                        full_response += token
                        token_buffer += token
                        
                        # 🔥 PERFORMANCE FIX: Only update the UI every 15 chars to stop Tkinter lag
                        if len(token_buffer) >= 15:
                            def append(t=token_buffer):
                                answer_box.configure(state="normal")
                                answer_box.insert("end", t)
                                answer_box.see("end")
                                answer_box.configure(state="disabled")
                            self.after(0, append)
                            token_buffer = "" # Clear the buffer after sending
                            
                # 🔥 NEW: Flush any leftover characters at the very end of the stream
                if token_buffer:
                    def append_final(t=token_buffer):
                        answer_box.configure(state="normal")
                        answer_box.insert("end", t)
                        answer_box.see("end")
                        answer_box.configure(state="disabled")
                    self.after(0, append_final)
                
                # ... (Keep the rest of your HIGHLIGHT PASS logic exactly the same below this) ...

                # 2. HIGHLIGHT PASS: Once stream is done, apply regex tags
                # 2. HIGHLIGHT PASS & EVIDENCE BUTTONS
                def apply_formatting():
                    answer_box.configure(state="normal")
                    answer_box.delete("1.0", "end")
                    
                    parts = re.split(r"(@[A-Za-z0-9_-]+|slide_\d+\.jpg|\[\d+:\d+\])", full_response)
                    for part in parts:
                        if part.startswith("@"):
                            answer_box.insert("end", part, "class_tag")
                        elif part.endswith(".jpg"):
                            start = answer_box.index("end")
                            answer_box.insert("end", part, "slide_tag")
                            end = answer_box.index("end")
                            answer_box.tag_add("slide_tag", start, end)
                        elif re.match(r"\[\d+:\d+\]", part):
                            answer_box.insert("end", part, "timestamp_tag")
                        else:
                            answer_box.insert("end", part)
                            
                    answer_box.see("end")
                    answer_box.configure(state="disabled")

                    # 🔥 NEW: Render Audio Evidence Buttons
                    # Clear old buttons
                    for widget in evidence_frame.winfo_children():
                        widget.destroy()

                    if hasattr(engine, "last_results") and engine.last_results:
                        ctk.CTkLabel(evidence_frame, text="Audio Sources:", font=ctk.CTkFont(family=self.FONT_FAMILY, size=13, weight="bold"), text_color=self.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
                        
                        for i, chunk in enumerate(engine.last_results):
                            start_sec = chunk.get("start_elapsed", 0)
                            raw_meeting_name = chunk.get("meeting", "Unknown")
                            meeting_dir_path = os.path.join("data", raw_meeting_name)
                            
                            # 🔥 NEW: Make the evidence button beautiful
                            parts = raw_meeting_name.split("_", 1)
                            if len(parts) == 2 and re.match(r"\d{4}-\d{2}-\d{2}", parts[0]):
                                pretty_name = parts[1].replace("_", " ")
                            else:
                                pretty_name = raw_meeting_name

                            mins, secs = int(start_sec // 60), int(start_sec % 60)
                            time_str = f"[{mins:02d}:{secs:02d}]"

                            btn = ctk.CTkButton(
                                evidence_frame,
                                text=f"▶ {pretty_name} {time_str}", # Renders "▶ Human Talk [04:12]"
                                height=32,
                                corner_radius=self.RADIUS_BTN,
                                fg_color=self.CARD,
                                hover_color="#1f2937",
                                text_color=self.ACCENT_SOFT,
                                border_color=self.BORDER,
                                border_width=1,
                                cursor="hand2",
                                command=lambda s=start_sec, m=meeting_dir_path: self._play_audio_from_elapsed(s, play_duration=10.0, meeting_dir=m)
                            )
                            btn.pack(side="left", padx=(0, 8))

                self.after(0, apply_formatting)

            threading.Thread(target=run, daemon=True).start()
            question_entry.delete(0, "end")

        # 🔥 NEW: Circular Send Button
        ask_btn = ctk.CTkButton(
            input_row,
            text="➤", 
            width=44,
            height=44, 
            corner_radius=22, # Circular
            fg_color=self.ACCENT,
            hover_color="#6b62ff",
            cursor="hand2",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=ask
        )
        ask_btn.pack(side="right", padx=(5, 8), pady=4)
        
        question_entry.bind("<Return>", lambda e: ask())
        question_entry.bind("<KeyRelease>", lambda e: self._show_class_suggestions(e, question_entry))
    # ================= AI SUGGESTION CHIPS =================
        # We populate the suggestion_frame we packed earlier
        suggestion_frame.configure(fg_color="transparent") 

        # Center container so the buttons sit nicely in the middle
        pill_container = ctk.CTkFrame(suggestion_frame, fg_color="transparent")
        pill_container.pack(anchor="center", pady=(10, 0))

        def trigger_suggestion(text):
            # 1. Clear the box
            question_entry.configure(state="normal")
            question_entry.delete(0, "end")
            # 2. Insert the suggestion
            question_entry.insert(0, text)
            # 3. Automatically trigger the AI!
            ask()

        # The quick-action prompts
        prompts = [
            "📝 What were the key takeaways?",
            "🧠 Explain the hardest concept simply",
            "🎯 Generate a practice question",
            "📏 List any formulas or definitions"
        ]

        # Build the pill-shaped buttons
        for p in prompts:
            btn = ctk.CTkButton(
                pill_container,
                text=p,
                height=34,
                corner_radius=17, # Perfectly round pill shape
                fg_color=self.CARD,
                hover_color="#1f2937",
                border_color=self.BORDER,
                border_width=1,
                text_color=self.TEXT_SECONDARY,
                font=ctk.CTkFont(family=self.FONT_FAMILY, size=13),
                cursor="hand2",
                command=lambda text=p: trigger_suggestion(text)
            )
            btn.pack(side="left", padx=8)  
    def _open_window_selector(self, on_confirm_callback=None):

     import pygetwindow as gw

     windows = [w for w in gw.getAllWindows() if w.title.strip()]
     # 🔍 DEBUG: print all detected windows
     for w in windows:
      print("WINDOW FOUND:", w.title)
     if not windows:
        print("[Window Selector] No windows found")
        return

     selector = ctk.CTkToplevel(self)
     selector.title("Select Meeting Window")
     selector.geometry("700x400")
     selector.grab_set()

     ctk.CTkLabel(
        selector,
        text="Select the Meeting Window to Record",
        font=ctk.CTkFont(size=18, weight="bold")
     ).pack(pady=20)

     # Optional: filter likely meeting windows
     
     filtered = windows

     titles = [w.title for w in filtered]

     selected_var = ctk.StringVar(value=titles[0])

     dropdown = ctk.CTkOptionMenu(
        selector,
        values=titles,
        variable=selected_var,
        width=600
    )
     dropdown.pack(pady=20)

     def confirm():
        selected_title = selected_var.get()

        for w in filtered:
            if w.title == selected_title:
                self._target_window = w
                break

        if self._target_window is not None:
            print("[Window Capture] Selected:", self._target_window.title)
        else:
            print("[Window Capture] No window selected")

        selector.destroy()

        if on_confirm_callback:
            on_confirm_callback()

     ctk.CTkButton(
        selector,
        text="Confirm Window",
        command=confirm
     ).pack(pady=20)
     
    def _start_capture_after_window(self):
        # ================= LIVE POLL =================
   

     if self._target_window is None:
        print("[Capture] No window selected")
        return

     print("[Capture] Starting capture...")

    # ================= STATE =================
     self.is_capturing = True
     self.start_time = time.time()
     self.timer_running = True
     self._live_polling = True
     self._run_live_poll()
     self._run_live_indexer() # 🔥 ADD THIS LINE
     
     threading.Thread(target=self._animate_waveform, daemon=True).start()

    # ================= UI =================
     self.status_pill.configure(text="Starting...", text_color=self.ACCENT)

     self.start_btn.configure(state="disabled")
     self.stop_btn.configure(state="normal", fg_color=self.DANGER)

    # ================= LIVE POLL =================
     self._run_live_poll()

    # ================= AUDIO =================
     try:
        device_index = self._get_default_output_device()

        print("[Audio] Selected device:", device_index)

        # ✅ Start audio (Let the engine find Stereo Mix itself)
        self.audio_engine = AudioSTTEngine(
           storage=self.storage # Changed back to match your original engine setup
        )

        threading.Thread(
            target=self.audio_engine.start_listening,
            daemon=True
        ).start()

        print("[Audio] Engine started")

     except Exception as e:
        print("[Audio ERROR]", e)
        self.audio_engine = None

    # ================= SLIDE CAPTURE =================
     if self.capture_mode == "audio_video":
        try:
            threading.Thread(
                target=self._capture_window_frames,
                daemon=True
            ).start()

            print("[Slides] Capture started")

        except Exception as e:
            print("[Slide Capture ERROR]", e)

    # ================= STATUS TEXT =================
     self.system_status_box.configure(state="normal")
     self.system_status_box.delete("1.0", "end")

     if self.capture_mode == "audio_video":
        msg = "🎙 Listening + capturing slides...\n\nRecording in progress."
     else:
        msg = "🎙 Listening (audio only)...\n\nRecording in progress."

     self.system_status_box.insert("end", msg)
     self.system_status_box.configure(state="disabled")

    # ================= TIMER =================
     threading.Thread(target=self._run_timer, daemon=True).start()

   
     self.status_pill.configure(text="● Capturing", text_color=self.SUCCESS)
     
     
    def _capture_window_frames(self):
        if self.capture_mode != "audio_video":
            return

        meeting_dir = self.storage.get_meeting_dir()
        if not meeting_dir:
            return
        
        slides_dir = os.path.join(meeting_dir, "slides")
        os.makedirs(slides_dir, exist_ok=True)

        from sentence_transformers import SentenceTransformer, util
        from PIL import Image
        import mss
        from typing import Any, cast # 🔥 Added for type safety
        
        vision_model = None
        try:
            print("[Window Capture] Loading CLIP...")
            vision_model = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            print(f"[Window Capture] CLIP failed: {e}")

        with mss.mss() as sct:
            last_capture_time = 0
            prev_emb = None  

            while self.is_capturing:
                try:
                    monitor = sct.monitors[1] 
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    if frame_bgr.mean() < 5:
                        time.sleep(1)
                        continue

                    current_time = time.time()

                    if current_time - last_capture_time > 5:
                        save_slide = False
                        current_emb = None # 🔥 Initialize to prevent 'unbound' error
                        
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                        pil_img = Image.fromarray(frame_rgb)

                        if vision_model:
                            # 🔥 Use cast to tell Pylance this specific call allows images
                            current_emb = vision_model.encode(cast(Any, pil_img))
                            
                            if prev_emb is None:
                                save_slide = True
                            else:
                                cos_sim = util.cos_sim(prev_emb, current_emb).item()
                                if cos_sim < 0.95:
                                    save_slide = True
                                    print(f"[Slide Semantic] Change: {cos_sim:.3f}")
                        else:
                            # Fallback pixel math
                            if prev_emb is None:
                                save_slide = True
                                prev_emb = frame_bgr.copy()
                            else:
                                diff = cv2.absdiff(prev_emb, frame_bgr)
                                if diff.mean() > 2.0:
                                    save_slide = True
                                    prev_emb = frame_bgr.copy()

                        if save_slide:
                            timestamp = int(current_time)
                            path = os.path.join(slides_dir, f"slide_{timestamp}.jpg")
                            cv2.imwrite(path, frame_bgr)
                            print(f"[Slide Saved] -> {path}")
                            
                            if vision_model and current_emb is not None:
                                prev_emb = current_emb
                            
                        last_capture_time = current_time

                    time.sleep(0.5)
                except Exception as e:
                    print("[Window Capture Error]", e)
                    time.sleep(1)

        print("[Window Capture] Stopped")
    def _get_formatted_meetings(self):
        """Reads raw folders and returns a map of { 'Display Name': 'raw_folder_name' } sorted by newest first."""
        base_dir = "data"
        if not os.path.exists(base_dir): return {}, []
        
        raw_folders = [name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))]
        # Sort reverse chronologically (newest dates first!)
        raw_folders.sort(reverse=True) 
        
        mapping = {}
        display_list = []
        
        for raw in raw_folders:
            parts = raw.split("_", 1)
            # If folder starts with a Date (YYYY-MM-DD), format it nicely
            if len(parts) == 2 and re.match(r"\d{4}-\d{2}-\d{2}", parts[0]):
                date_part, name_part = parts[0], parts[1]
                display_name = f"{name_part.replace('_', ' ')} ({date_part})"
            else:
                display_name = raw
                
            # Handle duplicates just in case
            original_display = display_name
            counter = 1
            while display_name in mapping:
                display_name = f"{original_display} #{counter}"
                counter += 1
                
            mapping[display_name] = raw
            display_list.append(display_name)
            
        return mapping, display_list 
    def _discover_classes(self):

     base_dir = "data"

     if not os.path.exists(base_dir):
        return []

     classes = [
        name for name in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, name))
    ]

     return classes
    def _show_class_suggestions(self, event, entry):
        text = entry.get()
        if "@" not in text:
            self._close_class_popup()
            return

        prefix = text.split("@")[-1].lower()
        meeting_map, _ = self._get_formatted_meetings()

        # Search by BOTH the clean name and the date
        matches = []
        for display_name, raw_folder in meeting_map.items():
            if prefix in display_name.lower() or prefix in raw_folder.lower():
                matches.append((display_name, raw_folder))

        if not matches:
            self._close_class_popup()
            return

        # create popup if it doesn't exist
        if not hasattr(self, "_class_popup") or not self._class_popup.winfo_exists():
            self._class_popup = ctk.CTkToplevel(entry)
            self._class_popup.overrideredirect(True)
            self._class_popup.attributes("-topmost", True)

            # container frame
            container = ctk.CTkFrame(
                self._class_popup,
                fg_color=self.CARD,
                border_color=self.BORDER,
                border_width=1,
                corner_radius=8
            )
            container.pack(fill="both", expand=True)

            # SCROLLABLE FRAME (Made slightly wider to fit nice names)
            self._class_popup_frame = ctk.CTkScrollableFrame(
                container,
                fg_color=self.CARD,
                height=200,
                width=320 
            )
            self._class_popup_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # clear previous buttons
        for child in self._class_popup_frame.winfo_children():
            child.destroy()

        # position popup under entry
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
 
        self._class_popup.geometry(f"+{x}+{y}")
        self._class_popup.lift()

        # Render the nice display names in the popup
        # Render the nice display names in the popup
        # Render the nice display names in the popup
        for display_name, raw_folder in matches:
            btn = ctk.CTkButton(
                self._class_popup_frame, 
                text=display_name, 
                height=28, 
                fg_color="transparent", 
                hover_color="#1f2937", 
                anchor="w", 
                font=ctk.CTkFont(family=self.FONT_FAMILY, size=13), 
                cursor="hand2"
                # ❌ REMOVED 'command=' from here
            )
            btn.pack(fill="x", padx=6, pady=2)

            # 🔥 FIX: Force a direct mouse-click bind. This bypasses the Tkinter focus bug!
            btn.bind("<Button-1>", lambda e, d=display_name: self._insert_class(entry, d))
            btn.pack(fill="x", padx=6, pady=2)
     
        
    def _close_class_popup(self):

     if hasattr(self, "_class_popup"):
        try:
            self._class_popup.destroy()
        except:
            pass     
        
    
     
    def _parse_class_mentions(self, question: str):
        import re
        import os
        
        # Find beautiful tags like @"Human Talk (2026-04-03)" AND old ugly tags just in case
        matches = re.findall(r'@"([^"]+)"', question) + re.findall(r'@([A-Za-z0-9_-]+)', question)
        
        # Get our translation map
        mapping, _ = self._get_formatted_meetings()
        
        seen = set()
        result = []
        
        for m in matches:
            if m in seen: continue
            seen.add(m)
            
            # Translate beautiful name back to raw folder!
            if m in mapping:
                result.append(mapping[m])
            # Or if it's already a raw folder, use it directly
            elif os.path.exists(os.path.join("data", m)):
                result.append(m)
                
        return result   

    def _remove_class_tags(self, question: str):
        import re
        # Strip out both quoted tags and unquoted tags before sending to LLM
        q = re.sub(r'@"[^"]+"', '', question)
        q = re.sub(r'@[A-Za-z0-9_-]+', '', q)
        return q.strip()
    
        
    def _insert_class(self, entry, class_name):
        print("DEBUG → Class selected from suggestion:", class_name)
        text = entry.get()
        if "@" not in text: return
        
        at_index = text.rfind("@")
        
        # 🔥 FIX: Wrap the beautiful name in quotes!
        new_text = text[:at_index] + f'@"{class_name}" '
        
        entry.delete(0, "end")
        entry.insert(0, new_text)
        entry.focus()
        self._close_class_popup()
     
    def _open_slide(self, slide_name):
        import os
        from PIL import Image

        slides_dir = "data"
        full_path = None
        
        # Hunt down the exact slide image
        for root, dirs, files in os.walk(slides_dir):
            if slide_name in files:
                full_path = os.path.join(root, slide_name)
                break
                
        if not full_path:
            print(f"[Slide Viewer] Slide not found: {slide_name}")
            return

        # 🔥 NEW: Sleek In-App Modal Viewer
        viewer = ctk.CTkToplevel(self)
        viewer.title(f"Slide Viewer - {slide_name}")
        viewer.geometry("900x700")
        viewer.configure(fg_color=self.BG)
        viewer.attributes("-topmost", True)
        viewer.focus_force()

        card = ctk.CTkFrame(viewer, fg_color=self.CARD, corner_radius=self.RADIUS_CARD, border_color=self.BORDER, border_width=1)
        card.pack(fill="both", expand=True, padx=30, pady=30)

        try:
            # Load and resize the image cleanly
            img = Image.open(full_path)
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

            img_label = ctk.CTkLabel(card, image=ctk_img, text="")
            img_label.pack(expand=True, fill="both", pady=(20, 0))
            
            ctk.CTkButton(card, text="Close Viewer", corner_radius=self.RADIUS_BTN, fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=self.FONT_FAMILY, size=13, weight="bold"), cursor="hand2", command=viewer.destroy).pack(pady=20)
            
        except Exception as e:
            ctk.CTkLabel(card, text=f"Error loading image:\n{e}", text_color=self.DANGER).pack(expand=True)
    def _update_capture_mode(self, value):
     if value == "Audio Only":
        self.capture_mode = "audio"
     else:
        self.capture_mode = "audio_video"

     print("[Capture Mode] Set to:", self.capture_mode)      
    def show_toast(self, message: str, type: str = "success"):
        """Displays a sleek, auto-dismissing sliding notification."""
        # Determine colors based on type
        bg_color = "#064e3b" if type == "success" else "#7f1d1d" if type == "error" else self.CARD
        text_color = "#34d399" if type == "success" else "#fca5a5" if type == "error" else self.TEXT_PRIMARY
        icon = "✅" if type == "success" else "❌" if type == "error" else "ℹ️"

        # Create the floating frame
        toast = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=self.RADIUS_CARD, border_color=self.BORDER, border_width=1)
        
        lbl = ctk.CTkLabel(toast, text=f"{icon}  {message}", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"), text_color=text_color)
        lbl.pack(padx=20, pady=12)

        # Place it completely off-screen at the bottom (rely=1.05)
        toast.place(relx=0.5, rely=1.05, anchor="center")

        # Smooth Slide-In Animation
        def slide_in(current_rely=1.05):
            if current_rely > 0.92:  # 0.92 is the final resting position
                current_rely -= 0.015
                toast.place(relx=0.5, rely=current_rely, anchor="center")
                self.after(10, lambda: slide_in(current_rely))
            else:
                # Once it arrives, wait 3 seconds, then slide out
                self.after(3000, slide_out)

        # Smooth Slide-Out Animation
        def slide_out(current_rely=0.92):
            # Check if window was closed while toast was visible
            if not toast.winfo_exists(): return 
            
            if current_rely < 1.05:
                current_rely += 0.015
                toast.place(relx=0.5, rely=current_rely, anchor="center")
                self.after(10, lambda: slide_out(current_rely))
            else:
                toast.destroy()

        # Kick off the animation
        slide_in()
        
    def open_cloud_modal(self):
        from rag.cloud_engine import CloudEngine
        import threading
        
        cloud = CloudEngine()
        data_size = cloud.get_local_size_mb()

        window = ctk.CTkToplevel(self)
        window.title("Cloud Sync")
        window.geometry("500x550")
        window.configure(fg_color=self.BG)
        window.grab_set()
        window.focus_force()

        # Header
        ctk.CTkLabel(window, text="☁️ Cloud Sync", font=ctk.CTkFont(family=self.FONT_FAMILY, size=28, weight="bold"), text_color=self.TEXT_PRIMARY).pack(pady=(40, 5))
        ctk.CTkLabel(window, text="Securely backup your AI brain.", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14), text_color=self.TEXT_SECONDARY).pack(pady=(0, 30))

        # Status Card
        card = ctk.CTkFrame(window, fg_color=self.CARD, corner_radius=self.RADIUS_CARD, border_color=self.BORDER, border_width=1)
        card.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(card, text="Local Data Size", font=ctk.CTkFont(family=self.FONT_FAMILY, size=13, weight="bold"), text_color=self.TEXT_SECONDARY).pack(pady=(20, 5))
        ctk.CTkLabel(card, text=f"{data_size} MB", font=ctk.CTkFont(family=self.FONT_FAMILY, size=32, weight="bold"), text_color=self.ACCENT).pack(pady=(0, 20))

        # Progress Bar (Hidden initially)
        progress = ctk.CTkProgressBar(window, height=6, fg_color=self.BG, progress_color=self.SUCCESS)
        progress.set(0)

        status_label = ctk.CTkLabel(window, text="", font=ctk.CTkFont(family=self.FONT_FAMILY, size=13), text_color=self.TEXT_SECONDARY)

        def start_sync():
            sync_btn.configure(state="disabled", text="Packaging Data...")
            progress.pack(fill="x", padx=60, pady=(20, 5))
            status_label.pack()
            progress.configure(mode="indeterminate")
            progress.start()

            def run_sync():
                try:
                    # 1. Zip the data
                    # 1. Zip the data
                    # 1. Zip the data
                    self.after(0, lambda: status_label.configure(text="Compressing local FAISS indexes & audio..."))
                    archive_path = cloud.package_brain_for_cloud()
                    
                    # 2. Upload to Google Drive!
                    self.after(0, lambda: status_label.configure(text="Authenticating & uploading to Google Drive..."))
                    cloud.upload_to_drive(archive_path)

                    # 3. Success UI
                    def success():
                        progress.stop()
                        progress.configure(mode="determinate")
                        progress.set(1.0)
                        status_label.configure(text=f"✅ Sync Complete! Backup saved at:\n{os.path.basename(archive_path)}", text_color=self.SUCCESS)
                        sync_btn.configure(text="Synced to Cloud", fg_color=self.BG, border_width=1, border_color=self.SUCCESS)
                        self.show_toast("Brain successfully backed up to the cloud!", type="success")

                    self.after(0, success)
                except Exception as e:
                    self.after(0, lambda: status_label.configure(text=f"❌ Sync Failed: {e}", text_color=self.DANGER))
                    self.after(0, lambda: progress.stop())
                    self.after(0, lambda: sync_btn.configure(state="normal", text="Retry Sync"))

            threading.Thread(target=run_sync, daemon=True).start()

        # 🔥 NEW: Container for side-by-side Backup/Restore buttons
        btn_container = ctk.CTkFrame(window, fg_color="transparent")
        btn_container.pack(fill="x", padx=40, pady=(30, 0))

        sync_btn = ctk.CTkButton(
            btn_container, 
            text="⬆️ Backup to Drive", 
            height=48,
            corner_radius=self.RADIUS_BTN,
            fg_color=self.ACCENT,
            hover_color="#4338ca",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=start_sync
        )
        sync_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def start_restore():
            # You can wire this up to cloud_engine.restore_from_drive() later!
            self.show_toast("Downloading Brain from Google Drive...", "success")

        restore_btn = ctk.CTkButton(
            btn_container, 
            text="⬇️ Restore Data", 
            height=48,
            corner_radius=self.RADIUS_BTN,
            fg_color="#1f2937",
            hover_color="#374151",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=14, weight="bold"),
            cursor="hand2",
            command=start_restore
        )
        restore_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
    def is_slide_semantically_different(self, img1_path, img2_PIL, threshold=0.92):
    # Load and encode images
     img1 = Image.open(img1_path).convert("RGB")
     img2 = img2_PIL.convert("RGB") if hasattr(img2_PIL, "convert") else img2_PIL

     emb1 = self.vision_model.encode([cast(Any, img1)], convert_to_tensor=True)[0]
     emb2 = self.vision_model.encode([cast(Any, img2)], convert_to_tensor=True)[0]
    
    # Calculate Cosine Similarity
     cos_sim = util.cos_sim(emb1, emb2)
    
    # If similarity is < 0.92, the content is significantly different
    
     return cos_sim.item() < threshold  
    def _hard_exit_app(self):
        """Forces the application and all background AI threads to terminate completely."""
        print("[System] Shutting down AI Operating System...")
        import sys
        self.quit()      # Stops the Tkinter mainloop
        sys.exit(0)      
    def _log_out(self):
        print("[Auth] Logging out user...")
        
        # 1. Stop any active recording/audio to prevent background leaks
        if self.is_capturing:
            self.stop_capture()
        self._pause_audio()
        
        # 2. Reset user state
        self.current_user = None
        self.brand_sub.configure(text="AI Study OS")
        
        # 3. Close any open floating windows
        if hasattr(self, "dash_overlay") and self.dash_overlay.winfo_exists():
            self.close_dashboard_overlay()
        if hasattr(self, "schedule_overlay") and self.schedule_overlay.winfo_exists():
            self.close_schedule_overlay()
            
        # 4. Rebuild and summon the login lock screen
        self._build_login_screen()
        
    def open_settings_modal(self):
        import json
        import os

        window = ctk.CTkToplevel(self)
        window.title("Settings")
        window.geometry("600x650")
        window.configure(fg_color=self.BG)
        window.grab_set()
        window.focus_force()

        # --- Load Existing Settings (if any) ---
        config_path = "data/config.json"
        current_config = {"mic": "Default System Microphone", "engine": "Local Ollama (Llama 3)", "api_key": ""}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    current_config.update(json.load(f))
            except: pass

        # Header
        ctk.CTkLabel(window, text="⚙️ Settings", font=ctk.CTkFont(family=self.FONT_FAMILY, size=28, weight="bold"), text_color=self.TEXT_PRIMARY).pack(pady=(40, 5))
        ctk.CTkLabel(window, text="Configure your AI Study OS hardware and models.", font=ctk.CTkFont(family=self.FONT_FAMILY, size=14), text_color=self.TEXT_SECONDARY).pack(pady=(0, 30))

        scroll = ctk.CTkScrollableFrame(window, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        # --- Audio Settings Card ---
        audio_card = ctk.CTkFrame(scroll, fg_color=self.CARD, corner_radius=16, border_color=self.BORDER, border_width=1)
        audio_card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(audio_card, text="Microphone Input", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 5))
        
        try:
            from typing import Dict, Any, cast
            devices = cast(list[Dict[str, Any]], sd.query_devices())
            mics = [str(d['name']) for d in devices if int(d.get('max_input_channels', 0)) > 0]
            mics = list(set(mics)) 
        except Exception:
            mics = ["Default System Microphone"]

        mic_var = ctk.StringVar(value=current_config["mic"] if current_config["mic"] in mics else (mics[0] if mics else "Default System Microphone"))
        ctk.CTkOptionMenu(audio_card, values=mics, variable=mic_var, fg_color="#1c192b", button_color="#1c192b", button_hover_color="#2f294d", height=40).pack(fill="x", padx=20, pady=(0, 20))

        # --- AI Engine Card ---
        ai_card = ctk.CTkFrame(scroll, fg_color=self.CARD, corner_radius=16, border_color=self.BORDER, border_width=1)
        ai_card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(ai_card, text="AI Engine Selection", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 5))
        
        model_var = ctk.StringVar(value=current_config["engine"])
        api_key_var = ctk.StringVar(value=current_config["api_key"])

        # Dynamic API Key Frame (Hidden by default)
        api_frame = ctk.CTkFrame(ai_card, fg_color="transparent")
        ctk.CTkLabel(api_frame, text="API Key", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(10, 5))
        api_entry = ctk.CTkEntry(api_frame, textvariable=api_key_var, show="*", height=40, placeholder_text="sk-...", fg_color="#0b0813", border_color=self.BORDER)
        api_entry.pack(fill="x", padx=20, pady=(0, 20))

        # Animation logic: Show/Hide API Key box based on dropdown
        def on_model_change(choice):
            if choice == "Local Ollama":
              api_frame.pack_forget()
            else:
              api_frame.pack(fill="x")

        dropdown = ctk.CTkOptionMenu(
    ai_card, 
    values=["Local Ollama", "Auto-Detect (Paste Key)", "OpenAI (GPT-4o)", "Anthropic (Claude 3.5)", "OpenRouter"], 
    variable=model_var, 
    command=on_model_change, fg_color="#1c192b", button_color="#1c192b", button_hover_color="#2f294d", height=40)
        dropdown.pack(fill="x", padx=20, pady=(0, 20))
        
        # Trigger once to set initial state
        on_model_change(model_var.get())

        # --- Save Logic ---
        def save_preferences():
            new_config = {
                "mic": mic_var.get(),
                "engine": model_var.get(),
                "api_key": api_key_var.get() if "Ollama" not in model_var.get() else ""
            }
            os.makedirs("data", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(new_config, f, indent=4)
            
            self.show_system_notification("Settings Saved", f"Engine set to {new_config['engine']}")
            window.destroy()

        save_btn = ctk.CTkButton(scroll, text="Save Preferences", height=48, corner_radius=self.RADIUS_BTN, fg_color=self.ACCENT, hover_color=self.ACCENT_SOFT, font=ctk.CTkFont(size=15, weight="bold"), command=save_preferences)
        save_btn.pack(fill="x", pady=(10, 20))    

if __name__ == "__main__":
    app = MeetingSystemUI()
    app.mainloop()
    
    