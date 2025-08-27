import random
import json

class ThreatManager:
    def __init__(self):
        self.turn_counter = 0
        self.last_threat = -3  # Allow first threat after 8 turns
        self.threat_cooldown = 8
        self.enemy_revealed = False
        self.enemy_defeated = False
        self.enemy_profile = random.choice(self.load_enemies())  # Select enemy at start
        self.threat_history = []
        self.level_10_intro_shown = False


    def load_enemies(self, file_path="enemies_type.json"):
        with open(file_path, 'r') as file:
            return json.load(file)

    def advance_threat(self):
        if self.enemy_defeated:
            return
        self.threat_history.append({
            "turn_counter": self.turn_counter,
            "last_threat": self.last_threat,
            "enemy_revealed": self.enemy_revealed,
            "enemy_profile": self.enemy_profile,
            "enemy_defeated": self.enemy_defeated
        })
        self.turn_counter += 1
        if not self.enemy_revealed and self.should_start_threat():
            self.start_threat()

    def revert_threat(self):
        if self.threat_history:
            previous_state = self.threat_history.pop()
            self.turn_counter = previous_state["turn_counter"]
            self.last_threat = previous_state["last_threat"]
            self.enemy_revealed = previous_state["enemy_revealed"]
            self.enemy_profile = previous_state["enemy_profile"]
            self.enemy_defeated = previous_state["enemy_defeated"]
        else:
            self.turn_counter = 0
            self.last_threat = -8
            self.enemy_revealed = False
            self.enemy_defeated = False
            self.enemy_profile = random.choice(self.load_enemies())

    def reset_threat(self):
        self.enemy_revealed = False
        self.enemy_defeated = False
        self.last_threat = self.turn_counter
        self.threat_history = []
        self.enemy_profile = random.choice(self.load_enemies())  # Select new enemy

    def should_start_threat(self):
        if self.enemy_revealed or self.enemy_defeated:
            return False
        return self.turn_counter >= 8 and self.turn_counter - self.last_threat >= self.threat_cooldown

    def start_threat(self):
        self.enemy_revealed = True
        self.threat_history.append({
            "turn_counter": self.turn_counter,
            "last_threat": self.last_threat,
            "enemy_revealed": self.enemy_revealed,
            "enemy_profile": self.enemy_profile,
            "enemy_defeated": self.enemy_defeated
        })

    def check_defeat(self, user_input):
        if not self.enemy_profile or not self.enemy_revealed:
            return False
        weaknesses = [w.lower() for w in self.enemy_profile['template']['weaknesses']]
        user_input_lower = user_input.lower()
        for weakness in weaknesses:
            if weakness in user_input_lower:
                self.enemy_defeated = True
                self.enemy_revealed = False
                return True
        return False

    def resolve_threat(self):
        if self.enemy_defeated:
            self.reset_threat()

    def get_enemy_description(self):
        if not self.enemy_revealed or not self.enemy_profile:
            return ""
        t = self.enemy_profile['type']
        p = self.enemy_profile['template']
        threat_guidance = (
            "Low threat (can fight easily)" if 1 <= p['threat_level'] <= 3 else
            "Medium threat (fight at your own loss)" if 4 <= p['threat_level'] <= 6 else
            "High threat (avoid conflict)" if 7 <= p['threat_level'] <= 9 else
            "Danger threat (run away at sight)"
        )
        return (
            f"A {t} emerges from the shadows of the {p['domain']}!\n"
            f"Threat Level: {p['threat_level']} ({threat_guidance})\n"
            f"Domain: {p['domain']}\n"
            f"Powers: {', '.join(p['powers'])}\n"
            f"Weaknesses: {', '.join(p['weaknesses'])}\n"
            f"Hint: {p.get('hint', 'No hint available.')}"
        )