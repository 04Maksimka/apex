"""Messier Object Guessing Game.

A game where players view a pinhole projection of a Messier object
and try to guess its Messier number.
"""
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime
import random
from typing import Tuple

from numpy._typing import NDArray

from src.messier.messier_catalog import MessierCatalog, MessierType
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.pinhole_projection.pinhole_projector import (
    ShotConditions, CameraConfig, Pinhole, PinholeConfig, ConstellationConfig
)
from src.planets_catalog.planet_catalog import PlanetCatalog


class MessierGame:
    """Messier object guessing game."""

    def __init__(self, num_rounds: int = 10):
        """
        Initialize the Messier game.

        :param num_rounds: Number of objects to guess
        """
        self.num_rounds = num_rounds
        self.current_round = 0
        self.score = 0
        self.messier_catalog = MessierCatalog()
        self.used_objects = set()

        # Initialize catalogs for visualization
        self.star_catalog = Catalog(catalog_name='hip_data.tsv', use_cache=True)
        self.planet_catalog = PlanetCatalog()

        # Camera configuration
        self.camera_config = CameraConfig.from_fov_and_aspect(
            fov_deg=60,  # Field of view
            aspect_ratio=1.5,
            height_pix=800
        )

        # Standard time for consistent visualization
        self.observation_time = datetime(2024, 1, 1, 0, 0, 0)

    def get_random_messier_object(self) -> Tuple[int, NDArray]:
        """Get a random Messier object that hasn't been used yet.
        
        :return: Tuple of (M number, object data)


        """
        all_objects = self.messier_catalog.get_all_objects()
        available_objects = [
            obj for obj in all_objects
            if obj['m_number'] not in self.used_objects
        ]

        if not available_objects:
            raise ValueError("No more unused Messier objects available!")

        chosen_object = random.choice(available_objects)
        self.used_objects.add(chosen_object['m_number'])

        return chosen_object['m_number'], chosen_object

    def create_pinhole_view(self, messier_object: NDArray,
                            show_object_marker: bool = True) -> Tuple[plt.Figure, plt.Axes]:
        """Create a pinhole projection centered on a Messier object.

        :param messier_object: Messier object data
        :type messier_object: NDArray
        :param show_object_marker: Whether to mark the Messier object location
        :type show_object_marker: bool:  (Default value = True)

        :return: Figure and axes
        :rtype: Tuple[plt.Figure, plt.Axes]
        """

        # Get the ECI coordinates of the Messier object
        center_direction = np.array([
            messier_object['x'],
            messier_object['y'],
            messier_object['z']
        ], dtype=np.float32)

        # Create shot conditions
        shot_cond = ShotConditions(
            center_direction=center_direction,
            tilt_angle=0.0,
        )

        # Create pinhole configuration
        config = PinholeConfig(
            local_time=self.observation_time,
            add_ticks=False,
            use_dark_mode=False,
            add_planets=False,
            add_ecliptic=False,
            add_equator=False,
            add_galactic_equator=False,
            add_equatorial_grid=True,
            add_constellations=True,
            add_constellations_names=False
        )

        # Constellation configuration
        constellation_config = ConstellationConfig(
            constellation_linewidth=0.5,
            constellation_alpha=0.5,
            constellation_color='lightgray'
        )

        # Create pinhole projector
        pinhole = Pinhole(
            shot_cond=shot_cond,
            camera_cfg=self.camera_config,
            config=config,
            constellation_config=constellation_config,
            catalog=self.star_catalog,
            planet_catalog=self.planet_catalog
        )

        # Generate the view
        constraints = CatalogConstraints(max_magnitude=6.5)
        fig, ax = pinhole.generate(constraints=constraints)
        ax.set_aspect('equal')

        # Add marker for the Messier object if requested
        if show_object_marker:
            # The object is at the center of the view
            center_x = self.camera_config.width / 2
            center_y = self.camera_config.height / 2

            # Calculate marker size based on object angular size
            marker_size = max(20, min(200, messier_object['size'] * 2))

            # Choose color based on object type
            color = MessierCatalog.get_type_color(MessierType(messier_object['obj_type']))

            ax.scatter(center_x, center_y, s=marker_size,
                       marker='o', facecolors='none',
                       edgecolors=color, linewidths=2, alpha=0.7)

            # Add a small dot at the exact center
            ax.scatter(center_x, center_y, s=10,
                       marker='.', c=color, alpha=0.9)

        return fig, ax

    def display_question(self, messier_object: NDArray):
        """Display the current question.

        :param messier_object: The Messier object data
        :type messier_object: NDArray
        """

        print("\n" + "="*60)
        print(f"Round {self.current_round + 1}/{self.num_rounds}")
        print("="*60)

        # Create and display the pinhole view
        fig, ax = self.create_pinhole_view(messier_object, show_object_marker=True)

        # Add title with hints
        obj_type_name = MessierCatalog.get_type_name(MessierType(messier_object['obj_type']))
        magnitude = messier_object['v_mag']
        size = messier_object['size']
        constellation = messier_object['constellation']

        title = (f"Guess the Messier Object!\n"
                 f"Type: {obj_type_name} | Magnitude: {magnitude:.1f} | "
                 f"Size: {size:.1f}' | Constellation: {constellation}")

        ax.set_title(title, fontsize=12, pad=20)

        plt.tight_layout()
        plt.show(block=False)
        plt.pause(0.1)

    def check_answer(self, guess: int, correct_answer: int,
                     messier_object: NDArray) -> bool:
        """Check if the guess is correct and provide feedback.

        :param guess: Player's guess
        :type guess: int
        :param correct_answer: Correct Messier number
        :type correct_answer: int
        :param messier_object: The Messier object data
        :type messier_object: NDArray

        :return: True if correct, False otherwise
        :rtype: bool
        """
        is_correct = (guess == correct_answer)

        if is_correct:
            print(f"\n✓ Correct! It's M{correct_answer}")
            self.score += 1
        else:
            print(f"\n✗ Wrong! The correct answer is M{correct_answer}")

        # Display additional information
        name = messier_object['name']
        if name:
            print(f"   Name: {name}")

        obj_type = MessierCatalog.get_type_name(MessierType(messier_object['obj_type']))
        print(f"   Type: {obj_type}")
        print(f"   Constellation: {messier_object['constellation']}")
        print(f"   Magnitude: {messier_object['v_mag']:.1f}")
        print(f"   Angular size: {messier_object['size']:.1f} arcminutes")

        return is_correct

    def play_round(self):
        """Play a single round of the game."""
        # Get a random Messier object
        m_number, messier_object = self.get_random_messier_object()

        # Display the question
        self.display_question(messier_object)

        # Get player's guess
        while True:
            try:
                guess_str = input(f"\nEnter Messier number (1-110): M")
                guess = int(guess_str)

                if 1 <= guess <= 110:
                    break
                else:
                    print("Please enter a number between 1 and 110.")
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\nGame interrupted!")
                return False

        # Check the answer
        self.check_answer(guess, m_number, messier_object)

        # Close the plot
        plt.close()

        return True

    def play(self):
        """Play the full game."""
        print("\n" + "="*60)
        print("MESSIER OBJECT GUESSING GAME")
        print("="*60)
        print(f"\nYou will be shown {self.num_rounds} Messier objects.")
        print("Try to guess each object's Messier number (M1-M110).")
        print("Each object will be shown in a pinhole projection")
        print("centered on the object (marked with a circle).")
        print("\nPress Ctrl+C at any time to quit.")
        print("\n" + "="*60)

        input("\nPress Enter to start...")

        # Play all rounds
        for round_num in range(self.num_rounds):
            self.current_round = round_num

            if not self.play_round():
                break

        # Display final score
        print("\n" + "="*60)
        print("GAME OVER!")
        print("="*60)
        print(f"Final Score: {self.score}/{self.current_round + 1}")

        if self.score == self.num_rounds:
            print("Perfect score! You're a Messier master! 🌟")
        elif self.score >= self.num_rounds * 0.7:
            print("Great job! You know your Messier objects! 🌠")
        elif self.score >= self.num_rounds * 0.4:
            print("Good effort! Keep studying the night sky! 🌙")
        else:
            print("Keep practicing! The universe is waiting! 🔭")

        print("="*60 + "\n")


def messier_game():
    """Main function to run the game."""

    print("\n" + "="*60)
    print("MESSIER OBJECT GUESSING GAME")
    print("="*60)

    # Ask how many rounds
    while True:
        try:
            num_rounds_str = input("\nHow many Messier objects do you want to guess? (1-110): ")
            num_rounds = int(num_rounds_str)

            if 1 <= num_rounds <= 110:
                break
            else:
                print("Please enter a number between 1 and 110.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            return

    # Create and play the game
    game = MessierGame(num_rounds=num_rounds)
    game.play()


if __name__ == '__main__':
    messier_game()