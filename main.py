from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QLabel, QSizePolicy, QLineEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from story_tree import TreeNode, build_path_from_prompt, build_current_prompt, system_prompt, query_ollama_streaming
from story_queue import add_to_queue, get_priority_memory, clear_priority_memory, list_priority_memory
from threat_manager import ThreatManager
import sys
import re

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.main_window.send_message()
        else:
            super().keyPressEvent(event)

class AIDungeonMasterChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Dungeon Master Chat")
        self.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")
        self.resize(800, 600)

        self.threat_manager = ThreatManager()
        self.include_full_path = False
        self.current_node = TreeNode("You are standing inside a mysterious dungeon. Behind you was the entrance of the dungeon that has bee closed now. You have three paths in front of you"
                                     "\n\n1) Moved forward which leads to a passage into dark hallways"
                                     "\n2) Move to your left, is a staircase that leads downwards"
                                     "\n3) Move to your right is a room, with a statue of a gargoyle"
                                     "\n\nThe decision is yours to make.", "Start")
        self.message_widgets = []
        self.stop_streaming = False

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        main_layout.addWidget(self.scroll_area)

        scroll_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_widget.setLayout(self.chat_layout)
        self.scroll_area.setWidget(scroll_widget)

        self.prompt_input = CustomTextEdit(self)
        self.prompt_input.setPlaceholderText("Enter your action or select an option (e.g., '1')...")
        self.prompt_input.setFixedHeight(60)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.prompt_input)

        memory_input_layout = QHBoxLayout()
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText("Enter memory with priority (e.g., '6: I have a sword')")
        self.memory_input.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        memory_input_layout.addWidget(self.memory_input)

        add_memory_button = QPushButton("Add Memory")
        add_memory_button.setFixedWidth(100)
        add_memory_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        add_memory_button.clicked.connect(self.add_memory)
        memory_input_layout.addWidget(add_memory_button)
        main_layout.addLayout(memory_input_layout)

        button_layout = QHBoxLayout()
        send_button = QPushButton("Send")
        send_button.setFixedWidth(80)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        send_button.clicked.connect(self.send_message)

        clear_button = QPushButton("Clear All")
        clear_button.setFixedWidth(80)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4C4C;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E04343;
            }
        """)
        clear_button.clicked.connect(self.clear_messages)

        show_memory_button = QPushButton("Show Memories")
        show_memory_button.setFixedWidth(120)
        show_memory_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
        """)
        show_memory_button.clicked.connect(self.show_memories)
        refresh_button = QPushButton("Refresh")
        refresh_button.setFixedWidth(100)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: black;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
        """)
        refresh_button.clicked.connect(self.refresh_prompt)

        
        button_layout.addWidget(send_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(show_memory_button)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.chat_layout.addStretch()
        self.add_message(self.current_node.state, is_user=False)

    def refresh_prompt(self):
        self.include_full_path = True
        self.add_message("🔁 Full story path will be included in the next response.", is_user=False)

    def add_memory(self):
        memory_text = self.memory_input.text().strip()
        if not memory_text:
            return
        match = re.match(r'^(\d+):\s*(.+)$', memory_text)
        if match:
            priority = int(match.group(1))
            fact = match.group(2).strip()
            add_to_queue(priority, fact)
            self.memory_input.clear()
            self.add_message(f"Added memory: {priority}: {fact}", is_user=False)
        else:
            self.add_message("Invalid format! Use 'priority: fact' (e.g., '6: I have a sword')", is_user=False)

    def show_memories(self):
        memories = list_priority_memory()
        if not memories:
            self.add_message("No memories in queue.", is_user=False)
            return
        memory_display = "📜 **Current Memories**\n\n"
        for priority, fact in sorted(memories, reverse=True):
            memory_display += f"Priority {priority}: {fact}\n"
        self.add_message(memory_display.strip(), is_user=False)

    def add_message(self, message, is_user, node=None):
        label = QLabel(message)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        label.setMaximumWidth(int(self.width() * 0.7))
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        alignment = Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft
        bg_color = "#4CAF50" if is_user else "#FFFFFF"
        text_color = "#FFFFFF" if is_user else "#000000"
        label.setStyleSheet(f"""
            QLabel {{
                padding: 12px;
                border-radius: 10px;
                background-color: {bg_color};
                color: {text_color};
                font-size: {'12px' if is_user else '14px'};
            }}
        """)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(10, 0, 10, 0)
        if is_user:
            h_layout.addStretch()
            h_layout.addWidget(label)
        else:
            h_layout.addWidget(label)
            h_layout.addStretch()

        container = QWidget()
        container.setLayout(h_layout)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        delete_button = QPushButton("Delete")
        delete_button.setFixedWidth(80)
        delete_button.setFixedHeight(30)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4C4C;
                color: white;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E04343;
            }
        """)
        delete_button.clicked.connect(lambda: self.delete_message(container, node))

        h_layout.addWidget(delete_button)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        self.chat_layout.insertSpacing(self.chat_layout.count() - 1, 10)
        self.message_widgets.append((container, is_user, node))
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def delete_message(self, container, node):
        if not node or not node.parent:
            return
        index = -1
        for i, (widget, is_user, widget_node) in enumerate(self.message_widgets):
            if widget == container:
                index = i
                break
        if index == -1:
            return
        if index + 1 < len(self.message_widgets) and not self.message_widgets[index + 1][1]:
            self.chat_layout.removeWidget(self.message_widgets[index + 1][0])
            self.message_widgets[index + 1][0].deleteLater()
            self.message_widgets.pop(index + 1)
        self.chat_layout.removeWidget(container)
        container.deleteLater()
        self.message_widgets.pop(index)
        self.current_node = node.parent
        self.threat_manager.revert_threat()
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def clear_messages(self):
        for widget, is_user, _ in self.message_widgets:
            self.chat_layout.removeWidget(widget)
            widget.deleteLater()
        self.message_widgets.clear()
        self.current_node = TreeNode("You are standing inside a mysterious dungeon. Behind you was the entrance of the dungeon that has bee closed now. You have three paths in front of you"
                                     "\n\n1) Moved forward which leads to a passage into dark hallways"
                                     "\n2) Move to your left, is a staircase that leads downwards"
                                     "\n3) Move to your right is a room, with a statue of a gargoyle"
                                     "\n\nThe decision is yours to make.", "Start")
        self.threat_manager = ThreatManager()
        clear_priority_memory()
        self.add_message(self.current_node.state, is_user=False)

    def stop_model_response(self):
        self.stop_streaming = True

    def send_message(self):
        user_input = self.prompt_input.toPlainText().strip()
        if not user_input:
            return

        if user_input.lower() in [
            "give me full path", "full path", "show path", 
            "story path so far", "path so far", 
            "give me full path so far", "give me full history"
        ]:
            path = self.current_node.getPath()
            path_display = "📜 **Story Path So Far**\n\n"
            for i, (state, choice, _) in enumerate(path):
                if i == 0:
                    path_display += f"🌟 Start: {state.strip()}\n\n"
                else:
                    path_display += f"🧭 Player chose: {choice.strip()}\n"
                    path_display += f"📖 Resulting situation:\n{state.strip()}\n\n"
            self.add_message(user_input, is_user=True)
            self.add_message(path_display.strip(), is_user=False)
            self.prompt_input.clear()
            return

        threat_state = {
            "turn_counter": self.threat_manager.turn_counter,
            "last_threat": self.threat_manager.last_threat,
            "enemy_revealed": self.threat_manager.enemy_revealed,
            "enemy_profile": self.threat_manager.enemy_profile,
            "enemy_defeated": self.threat_manager.enemy_defeated
        }
        new_node = TreeNode("", user_input.strip(), threat_state=threat_state)
        self.current_node.add_child(new_node)
        self.add_message(user_input, is_user=True, node=new_node)
        self.current_node = new_node
        self.prompt_input.clear()

        self.threat_manager.advance_threat()

        enemy = self.threat_manager.enemy_profile

        defeat_message = ""
        if self.threat_manager.enemy_revealed and enemy:
            if self.threat_manager.check_defeat(user_input):
                defeat_message = (
                    f"🎯 The {enemy['type']} succumbs to your {user_input.lower()}!\n"
                    f"{enemy['template']['death_behavior']}"
                )
                self.threat_manager.resolve_threat()
                self.add_message(defeat_message, is_user=False)
                self.add_message("The dungeon grows quiet again. What will you do? 1) Continue exploring, 2) Rest, 3) Check your inventory.", is_user=False)
                return


        memory_facts = get_priority_memory()
        memory_block = ""
        if memory_facts:
            memory_block = (
                "The following are **absolute facts** about the player. "
                "You MUST NOT contradict them. If the player attempts something that goes against these, correct them in a way that satisfies these facts.\n\n"
            )
            memory_block += "\n".join(f"- FACT: {fact}" for fact in memory_facts) + "\n\n"

        path_block = ""
        if self.include_full_path:
            path_block = build_path_from_prompt(self.current_node.getPath())
            self.include_full_path = False
        else:
            path_block = build_current_prompt(self.current_node.parent.state, self.current_node.choice)

        enemy_block = ""
        transition_block = ""
        if enemy and self.threat_manager.enemy_revealed:
            if self.threat_manager.turn_counter == self.threat_manager.last_threat:
                transition_block = (
                    f"You are to first transition the envrionment to the domain of the enemy before fully introducing them"
                    f" You have to transition the current scene to a scene that fits the domain of the enemy. It should be done seamlessly, and the domain of the enemy should not be changed. It should be exactly described."
                    )

            enemy_block = (
                f"Current Enemy: {enemy['type']}\n"
                f"Domain: {enemy['template']['domain']}\n"
                f"Powers: {', '.join(enemy['template']['powers'])}\n"
                f"Weaknesses: {', '.join(enemy['template']['weaknesses'])}\n"
                f"Hint: {enemy['template']['hint']}\n"
                f"Threat Level: {enemy['template']['threat_level']}"
                "You MUST select the current enemy ONLY from the following types: Fire Golem, Skeleton Warrior, Orc, Dragon. "
                "Do NOT invent new enemies. Narrate the scene based on the player's last action, incorporating the enemy's domain, but do not resolve actions, suggest plans, or make decisions for the player. "
                "Always end your response with three action options (e.g., 'What will you do? 1) Option A, 2) Option B, 3) Option C').\n\n"
            )
        death_rules_block = ""
        if enemy:
            threat_level = enemy["template"].get("threat_level", 0)
            if threat_level >= 10:
                death_rules_block = (
                    " Player Death Rules:\n"
                    f"- If the player does NOT flee (by using the word 'flee', 'run away', 'escape', or similar), you MUST kill them immediately."
                    f"- Any action involving fighting, dodging, blocking, or standing their ground must result in instant death."
                    f"- You MUST interpret all combat or hesitation as failure to flee. Do not be lenient."
                    )
                
            elif 7 <= threat_level <= 9:
                death_rules_block = (
                    "🪦 Player Death Rules:\n"
                    "- The enemy is a **high-level threat (7-9)**. If the player does NOT use a listed weakness, they MUST die.\n"
                    "- You must describe the player's death vividly using language such as:\n"
                    "  'rips through your chest', 'slams you against the wall with a deafening crack', 'you die', 'your vision fades'.\n"
                    "- Only spare them if they cleverly use a weakness.\n"
                )
            
        prompt = (
            system_prompt + "\n\n"
            + "Do NOT introduce any enemies in the narrative unless explicitly instructed in the 'Enemy Information' section. "
            "Focus on the dungeon environment and the player's actions, ensuring the scene aligns with the current context.\n\n"
            + memory_block
            + enemy_block
            + transition_block
            + death_rules_block
            + f"⚠️ Enemy Information:\n{self.threat_manager.get_enemy_description()}\n\n"
            + path_block + "\n\n"
            + "Describe the scene and the effects of the player's action without resolving the outcome or making decisions. "
            "If the player's action does not use a weakness when an enemy is present, describe its failure and repeat the hint. "
            "Do NOT introduce new enemies or conclude the encounter until the player uses a weakness to defeat the current enemy. "
            "Always provide exactly three action options at the end of your response."
        )

        model_label = QLabel("")
        model_label.setWordWrap(True)
        model_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        model_label.setMaximumWidth(int(self.width() * 0.7))
        model_label.setStyleSheet("""
            QLabel {
                padding: 12px;
                border-radius: 10px;
                background-color: #FFFFFF;
                color: #000000;
                font-size: 14px;
            }
        """)
        model_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        stop_button = QPushButton("Stop")
        stop_button.setFixedWidth(80)
        stop_button.setFixedHeight(30)
        stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4C4C;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E04343;
            }
        """)
        stop_button.clicked.connect(self.stop_model_response)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(10, 0, 10, 0)
        h_layout.addWidget(model_label)
        h_layout.addWidget(stop_button)
        h_layout.addStretch()

        container = QWidget()
        container.setLayout(h_layout)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        self.chat_layout.insertSpacing(self.chat_layout.count() - 1, 10)
        self.message_widgets.append((container, False, None))
        QApplication.processEvents()

        self.stop_streaming = False
        full_text = ""
        for chunk in query_ollama_streaming(prompt):
            if self.stop_streaming:
                model_label.setText(full_text + "\n[Stopped by user]")
                stop_button.hide()
                break
            full_text += chunk
            model_label.setText(full_text)
            QApplication.processEvents()
            QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()))

        stop_button.hide()
        self.current_node.state = full_text.strip()
    # def player_fled(self, user_input: str) -> bool:
    #     flee_words = ["flee", "run", "escape", "retreat", "sprint", "get away"]
    #     return any(word in user_input.lower() for word in flee_words)
    
    # def send_message(self):
    #     user_input = self.prompt_input.toPlainText().strip()
    #     if not user_input:
    #         return

    #     # === Special Commands ===
    #     if user_input.lower() in [
    #         "give me full path", "full path", "show path", 
    #         "story path so far", "path so far", 
    #         "give me full path so far", "give me full history"
    #     ]:
    #         path = self.current_node.getPath()
    #         path_display = "📜 **Story Path So Far**\n\n"
    #         for i, (state, choice, _) in enumerate(path):
    #             if i == 0:
    #                 path_display += f"🌟 Start: {state.strip()}\n\n"
    #             else:
    #                 path_display += f"🧭 Player chose: {choice.strip()}\n"
    #                 path_display += f"📖 Resulting situation:\n{state.strip()}\n\n"
    #         self.add_message(user_input, is_user=True)
    #         self.add_message(path_display.strip(), is_user=False)
    #         self.prompt_input.clear()
    #         return

    #     # === Update Tree State ===
    #     threat_state = {
    #         "turn_counter": self.threat_manager.turn_counter,
    #         "last_threat": self.threat_manager.last_threat,
    #         "enemy_revealed": self.threat_manager.enemy_revealed,
    #         "enemy_profile": self.threat_manager.enemy_profile,
    #         "enemy_defeated": self.threat_manager.enemy_defeated
    #     }
    #     new_node = TreeNode("", user_input.strip(), threat_state=threat_state)
    #     self.current_node.add_child(new_node)
    #     self.add_message(user_input, is_user=True, node=new_node)
    #     self.current_node = new_node
    #     self.prompt_input.clear()

    #     # === Advance Threat System ===
    #     self.threat_manager.advance_threat()
    #     enemy = self.threat_manager.enemy_profile

    #     # === Check for Defeat ===
    #     if self.threat_manager.enemy_revealed and enemy:
    #         if self.threat_manager.check_defeat(user_input):
    #             defeat_message = (
    #                 f"🎯 The {enemy['type']} succumbs to your {user_input.lower()}!\n"
    #                 f"{enemy['template']['death_behavior']}"
    #             )
    #             self.threat_manager.resolve_threat()
    #             self.add_message(defeat_message, is_user=False)
    #             self.add_message("The dungeon grows quiet again. What will you do? 1) Continue exploring, 2) Rest, 3) Check your inventory.", is_user=False)
    #             return

    #     # === MODE SWITCH LOGIC ===
    #     threat_level = enemy["template"].get("threat_level", 0) if enemy else 0
    #     in_death_mode = threat_level >= 10

    
    #     if in_death_mode:
    #         if not self.threat_manager.level_10_intro_shown:
    #             self.threat_manager.level_10_intro_shown = True
    #             intro_block = (
    #                 "⚠️ LEVEL 10 ENEMY DETECTED\n"
    #                 "- Introduce the enemy for the first time.\n"
    #                 "- Describe its appearance, presence, and domain vividly and terrifyingly.\n"
    #                 "- Make it **crystal clear** that the player should **flee immediately**.\n"
    #                 "- Do NOT kill the player yet — just create overwhelming fear.\n"
    #                 "- End with 3 options. One must be fleeing.\n"
    #             )
    #             prompt = intro_block + "\n\n🧍 Player Action:\n" + user_input
    #         else:
    #             if not self.player_fled(user_input):
    #                 death_block = (
    #                     "☠️ DEATH ENFORCEMENT MODE\n"
    #                     "- The enemy is a level 10 threat.\n"
    #                     "- The player ignored warnings and chose to fight or stay.\n"
    #                     "- You must **kill them immediately**.\n"
    #                     "- No mercy. No hesitation.\n"
    #                     "- Use vivid death phrases like:\n"
    #                     "  'rips through your chest', 'you collapse', 'your vision fades', 'you die'.\n"
    #                     "- End the story for this path.\n"
    #                 )
    #                 prompt = death_block + "\n\n🧍 Player Action:\n" + user_input
    #             else:
    #                 # Player successfully fled
    #                 self.threat_manager.resolve_threat()
    #                 self.threat_manager.level_10_intro_shown = False
    #                 # Now fall back to normal prompt below (let story continue)
    #                 in_death_mode = False


    #     # === Build Prompt: NORMAL MODE ===
    #     else:
    #         memory_block = ""
    #         memory_facts = get_priority_memory()
    #         if memory_facts:
    #             memory_block = (
    #                 "The following are **absolute facts** about the player. "
    #                 "You MUST NOT contradict them.\n\n"
    #             )
    #             memory_block += "\n".join(f"- FACT: {fact}" for fact in memory_facts) + "\n\n"

    #         transition_block = ""
    #         if enemy and self.threat_manager.enemy_revealed and self.threat_manager.turn_counter == self.threat_manager.last_threat:
    #             transition_block = (
    #                 "You are to first transition the environment to the domain of the enemy before fully introducing them. "
    #                 "This transition must be seamless and match the enemy's domain precisely.\n\n"
    #             )

    #         enemy_block = ""
    #         if enemy and self.threat_manager.enemy_revealed:
    #             enemy_block = (
    #                 f"Current Enemy: {enemy['type']}\n"
    #                 f"Domain: {enemy['template']['domain']}\n"
    #                 f"Powers: {', '.join(enemy['template']['powers'])}\n"
    #                 f"Weaknesses: {', '.join(enemy['template']['weaknesses'])}\n"
    #                 f"Hint: {enemy['template']['hint']}\n"
    #                 f"Threat Level: {threat_level}\n"
    #                 "You MUST select the current enemy ONLY from: Fire Golem, Skeleton Warrior, Orc, Dragon. "
    #                 "Do NOT invent new enemies. Use the domain, powers, and weaknesses as context. "
    #                 "Do NOT resolve the player's choice. Always end with three action options.\n\n"
    #             )

    #         death_rules_block = ""
    #         if 7 <= threat_level <= 9:
    #             death_rules_block = (
    #                 "🪦 Player Death Rules:\n"
    #                 "- The enemy is a high-level threat (7-9). If the player does NOT use a weakness, they MUST die.\n"
    #                 "- Describe the death vividly if weakness is ignored.\n\n"
    #             )

    #         if self.include_full_path:
    #             path_block = build_path_from_prompt(self.current_node.getPath())
    #             self.include_full_path = False
    #         else:
    #             path_block = build_current_prompt(self.current_node.parent.state, self.current_node.choice)

    #         prompt = (
    #             system_prompt + "\n\n"
    #             + "Do NOT invent enemies. Do NOT resolve player's choices. Always give 3 options.\n\n"
    #             + memory_block
    #             + enemy_block
    #             + transition_block
    #             + death_rules_block
    #             + f"⚠️ Enemy Information:\n{self.threat_manager.get_enemy_description()}\n\n"
    #             + path_block + "\n\n"
    #             + "Respond to the player’s last input naturally and narratively."
    #         )

    #     # === GUI Rendering and Streaming ===
    #     model_label = QLabel("")
    #     model_label.setWordWrap(True)
    #     model_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    #     model_label.setMaximumWidth(int(self.width() * 0.7))
    #     model_label.setStyleSheet("""
    #         QLabel {
    #             padding: 12px;
    #             border-radius: 10px;
    #             background-color: #FFFFFF;
    #             color: #000000;
    #             font-size: 14px;
    #         }
    #     """)
    #     model_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    #     stop_button = QPushButton("Stop")
    #     stop_button.setFixedWidth(80)
    #     stop_button.setFixedHeight(30)
    #     stop_button.setStyleSheet("""
    #         QPushButton {
    #             background-color: #FF4C4C;
    #             color: white;
    #             border-radius: 10px;
    #             padding: 5px 10px;
    #             font-size: 12px;
    #         }
    #         QPushButton:hover {
    #             background-color: #E04343;
    #         }
    #     """)
    #     stop_button.clicked.connect(self.stop_model_response)

    #     h_layout = QHBoxLayout()
    #     h_layout.setContentsMargins(10, 0, 10, 0)
    #     h_layout.addWidget(model_label)
    #     h_layout.addWidget(stop_button)
    #     h_layout.addStretch()

    #     container = QWidget()
    #     container.setLayout(h_layout)
    #     container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    #     self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
    #     self.chat_layout.insertSpacing(self.chat_layout.count() - 1, 10)
    #     self.message_widgets.append((container, False, None))
    #     QApplication.processEvents()

    #     # === Streaming Output ===
    #     self.stop_streaming = False
    #     full_text = ""
    #     for chunk in query_ollama_streaming(prompt):
    #         if self.stop_streaming:
    #             model_label.setText(full_text + "\n[Stopped by user]")
    #             stop_button.hide()
    #             break
    #         full_text += chunk
    #         model_label.setText(full_text)
    #         QApplication.processEvents()
    #         QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
    #             self.scroll_area.verticalScrollBar().maximum()))

    #     stop_button.hide()
    #     self.current_node.state = full_text.strip()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIDungeonMasterChat()
    window.show()
    sys.exit(app.exec())