from dataclasses import dataclass
from config.game import (MODE_STANDARD, MODE_DECAY, MODE_POWER, MODE_STAR, 
                       MODE_LIMITLESS, MODE_EVERYTHING)

@dataclass
class RuleSet:
    name: str
    double_free_three: bool = True
    decay_enabled: bool = False
    power_stones: bool = False
    shooting_star: bool = False

def get_rules_for_mode(mode_name: str) -> RuleSet:
    """Return the corresponding RuleSet for the selected game mode."""
    if mode_name == MODE_DECAY:
        return RuleSet(name=mode_name, double_free_three=False, decay_enabled=True)
    elif mode_name == MODE_POWER:
        return RuleSet(name=mode_name, double_free_three=False, power_stones=True)
    elif mode_name == MODE_STAR:
        return RuleSet(name=mode_name, double_free_three=False, shooting_star=True)
    elif mode_name == MODE_LIMITLESS:
        return RuleSet(name=mode_name, double_free_three=False)
    elif mode_name == MODE_EVERYTHING:
        return RuleSet(
            name=mode_name,
            double_free_three=False,
            decay_enabled=True,
            power_stones=True,
            shooting_star=True
        )
    # Default to Standard
    return RuleSet(name=MODE_STANDARD, double_free_three=True)
