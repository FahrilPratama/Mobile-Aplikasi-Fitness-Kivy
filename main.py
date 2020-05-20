from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.image import Image
from os import walk
from functools import partial
from workoutbanner import WorkoutsBanner
import requests
import json


class HomeScreen(Screen):
    pass


class LabelButton(ButtonBehavior, Label):
    pass


class ImageButton(ButtonBehavior, Image):
    pass


class SettingsScreen(Screen):
    pass


class ChangeAvatarScreen(Screen):
    pass


GUI = Builder.load_file("main.kv")


class MainApp(App):
    my_friend_id = 1

    def build(self):
        return GUI

    def on_start(self):
        # Get database data
        result = requests.get("https://fitnessapp-kivy.firebaseio.com/" + str(self.my_friend_id) + ".json")
        data = json.loads(result.content.decode())

        # Populate avatar grid
        avatar_grid = self.root.ids['change_avatar_screen'].ids['avatar_grid']
        for root_dir, folders, files in walk("icons/avatars"):
            for f in files:
                img = ImageButton(source="icons/avatars/" + f, on_release=partial(self.change_avatar, f))
                avatar_grid.add_widget(img)

        # Update avatar image
        avatar_image = self.root.ids['avatar_image']
        avatar_image.source = "icons/avatars/" + data['avatar']

        # Update streak label
        label_streak = self.root.ids['home_screen'].ids['streak_label']
        label_streak.text = str(data['streak']) + " Hari Berturut-turut"

        # Update id label
        friend_id_label = self.root.ids['settings_screen'].ids['friend_id_label']
        friend_id_label.text = "ID: " + str(self.my_friend_id)

        # Get data workouts
        banner_grid = self.root.ids['home_screen'].ids['banner_grid']
        workouts = data['workouts'][1:]
        for workout in workouts:
            widget_banner = WorkoutsBanner(workout_image=workout['workout_image'], description=workout['description'],
                                           type_image=workout['type_image'], number=workout['number'],
                                           units=workout['units'], likes=workout['likes'])
            banner_grid.add_widget(widget_banner)

    def change_avatar(self, image, widget_id):
        # Change avatar in app
        avatar_image = self.root.ids['avatar_image']
        avatar_image.source = "icons/avatars/" + image

        # Change avatar in firebase
        my_avatar = '{"avatar": "%s"}' % image
        requests.patch("https://fitnessapp-kivy.firebaseio.com/" + str(self.my_friend_id) + ".json", data=my_avatar)

        self.change_screen("settings_screen")

    def change_screen(self, screen_name):
        screen_manager = self.root.ids['screen_manager']
        screen_manager.transition
        screen_manager.current = screen_name


if __name__ == '__main__':
    MainApp().run()
