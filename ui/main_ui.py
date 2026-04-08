import customtkinter as ctk

ctk.set_appearance_mode("dark")


class MeetingSystemUI(ctk.CTk):

    # ===== 10/10 Premium Dark Palette =====
    BG = "#0a0d14"
    CARD = "#0f1624"

    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"

    ACCENT_MAIN = "#7c7cff"   # violet
    ACCENT_ALT = "#38bdf8"    # cyan
    ACCENT_HOVER = "#9f9fff"

    SUCCESS = "#22c55e"
    DANGER = "#ef4444"
    DISABLED = "#374151"

    BORDER = "#1e293b"

    def __init__(self):
        super().__init__()

        self.is_capturing = False

        self.title("meetingSystem")
        self.geometry("1100x720")
        self.resizable(False, False)
        self.configure(fg_color=self.BG)

        # ================= ROOT =================
        self.root = ctk.CTkFrame(self, fg_color=self.BG)
        self.root.pack(fill="both", expand=True, padx=40, pady=32)

        # ================= TOP BAR =================
        self.top_bar = ctk.CTkFrame(self.root, fg_color=self.BG)
        self.top_bar.pack(fill="x", pady=(0, 28))

        self.brand = ctk.CTkFrame(self.top_bar, fg_color=self.BG)
        self.brand.pack(side="left")

        self.brand_label = ctk.CTkLabel(
            self.brand,
            text="meetingSystem",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        self.brand_label.pack(anchor="w")

        self.brand_sub = ctk.CTkLabel(
            self.brand,
            text="Your personal academic companion",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_SECONDARY
        )
        self.brand_sub.pack(anchor="w", pady=(2, 0))

        self.top_right = ctk.CTkFrame(self.top_bar, fg_color=self.BG)
        self.top_right.pack(side="right")

        self.status_pill = ctk.CTkLabel(
            self.top_right,
            text="● Not capturing",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.TEXT_SECONDARY,
            fg_color=self.CARD,
            corner_radius=999,
            padx=16,
            pady=8
        )
        self.status_pill.pack(side="left")

        # ================= DIVIDER =================
        self.divider = ctk.CTkFrame(self.root, height=1, fg_color=self.BORDER)
        self.divider.pack(fill="x", pady=(0, 24))

        # ================= CAPTURE CARD =================
        self.capture_card = self._card()
        self.capture_card.pack(fill="x", pady=12)

        self.capture_title = ctk.CTkLabel(
            self.capture_card,
            text="Live capture",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        self.capture_title.pack(anchor="w", padx=28, pady=(22, 6))

        self.capture_desc = ctk.CTkLabel(
            self.capture_card,
            text="Start listening to your class and let me remember everything for you.",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_SECONDARY
        )
        self.capture_desc.pack(anchor="w", padx=28, pady=(0, 18))

        self.capture_btns = ctk.CTkFrame(self.capture_card, fg_color=self.CARD)
        self.capture_btns.pack(anchor="w", padx=28, pady=(0, 22))

        # ===== PREMIUM BUTTONS =====
        self.start_btn = ctk.CTkButton(
            self.capture_btns,
            text="Start capture",
            height=52,
            width=210,
            corner_radius=14,
            fg_color=self.ACCENT_MAIN,
            hover_color=self.ACCENT_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_capture,
            border_width=0
        )
        self.start_btn.pack(side="left")
        self._add_premium_glow(self.start_btn, self.ACCENT_MAIN)

        self.stop_btn = ctk.CTkButton(
            self.capture_btns,
            text="Stop",
            height=52,
            width=130,
            corner_radius=14,
            fg_color=self.DISABLED,
            hover_color="#4b5563",
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled",
            command=self.stop_capture,
            border_width=0
        )
        self.stop_btn.pack(side="left", padx=(16, 0))
        self._add_premium_glow(self.stop_btn, self.DANGER)

        # ================= ASK CARD =================
        self.ask_card = self._card()
        self.ask_card.pack(fill="x", pady=12)

        self.ask_title = ctk.CTkLabel(
            self.ask_card,
            text="Ask about your class",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT_PRIMARY
        )
        self.ask_title.pack(anchor="w", padx=28, pady=(22, 6))

        self.ask_entry = ctk.CTkEntry(
            self.ask_card,
            placeholder_text="Explain normalization, What did I miss after 10:30?",
            height=48,
            corner_radius=14,
            fg_color="#0b1220",
            text_color=self.TEXT_PRIMARY,
            placeholder_text_color=self.TEXT_SECONDARY,
            border_color=self.BORDER,
            font=ctk.CTkFont(size=15)
        )
        self.ask_entry.pack(fill="x", padx=28, pady=(0, 12))

        self.ask_btn = ctk.CTkButton(
            self.ask_card,
            text="Ask",
            height=48,
            width=150,
            corner_radius=14,
            fg_color=self.ACCENT_ALT,
            hover_color="#67e8f9",
            text_color="#020617",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.ask_question,
            border_width=0
        )
        self.ask_btn.pack(anchor="e", padx=28, pady=(0, 22))
        self._add_premium_glow(self.ask_btn, self.ACCENT_ALT)

        # ================= ANSWER CARD =================
        self.answer_card = self._card()
        self.answer_card.pack(fill="both", expand=True, pady=12)

        self.answer_label = ctk.CTkLabel(
            self.answer_card,
            text="I’m here to help you remember and understand your classes.\nAsk me anything whenever you’re ready.",
            font=ctk.CTkFont(size=15),
            text_color=self.TEXT_PRIMARY,
            wraplength=900,
            justify="left"
        )
        self.answer_label.pack(anchor="w", padx=28, pady=28)

    # ================= HELPERS =================

    def _card(self):
        return ctk.CTkFrame(
            self.root,
            fg_color=self.CARD,
            corner_radius=18,
            border_color=self.BORDER,
            border_width=1
        )

    def _add_premium_glow(self, widget, glow_color):
        def on_enter(e):
            widget.configure(border_width=2, border_color=glow_color)

        def on_leave(e):
            widget.configure(border_width=0)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # ================= LOGIC =================

    def start_capture(self):
        if self.is_capturing:
            return

        self.is_capturing = True

        self.status_pill.configure(text="● Listening", text_color=self.SUCCESS)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", fg_color=self.DANGER, hover_color="#dc2626")

        self.answer_label.configure(
            text="I’m listening to your class now.\nI’ll remember everything so you can revise later."
        )

    def stop_capture(self):
        if not self.is_capturing:
            return

        self.is_capturing = False

        self.status_pill.configure(text="● Not capturing", text_color=self.TEXT_SECONDARY)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled", fg_color=self.DISABLED, hover_color="#4b5563")

        self.answer_label.configure(
            text="Class saved.\nYou can come back anytime to revise or ask questions."
        )

    def ask_question(self):
        q = self.ask_entry.get().strip()

        if not q:
            self.answer_label.configure(text="Ask me something about your class.")
            return

        self.answer_label.configure(
            text=f"You asked: \"{q}\"\n\nOnce capture is connected, I’ll answer based on what was taught in class."
        )
        self.ask_entry.delete(0, "end")


if __name__ == "__main__":
    app = MeetingSystemUI()
    app.mainloop()
