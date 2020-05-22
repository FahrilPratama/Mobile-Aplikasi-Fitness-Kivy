from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, WipeTransition, SwapTransition, SlideTransition, NoTransition, CardTransition
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from os import walk
from functools import partial
from datetime import datetime
from workoutbanner import WorkoutsBanner
from myfirebase import MyFirebase
import requests
import json
import helperfunctions


class HomeScreen(Screen):
    pass


class AddFriendScreen(Screen):
    pass


class AddWorkoutScreen(Screen):
    pass

class FriendsListScreen(Screen):
    pass


class LabelButton(ButtonBehavior, Label):
    pass


class ImageButton(ButtonBehavior, Image):
    pass


class LoginScreen(Screen):
    pass


class RegisterScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class ChangeAvatarScreen(Screen):
    pass


class Popups(FloatLayout):
    pass


GUI = Builder.load_file("main.kv")


class MainApp(App):
    my_friend_id = ""
    popupWindow = Popup()
    popup_message = ""
    status_popup = ""
    workout_image = None
    workout_image_widget = ""
    option_choice = None

    def build(self):
        self.my_firebase = MyFirebase()
        return GUI

    def on_start(self):
        # Choose the correct time icon to show based on the current hour of day
        now = datetime.now()
        hour = now.hour
        if hour <= 6:
            self.root.ids['time_indicator1'].opacity = 1
        elif hour <= 12:
            self.root.ids['time_indicator2'].opacity = 1
        elif hour <= 18:
            self.root.ids['time_indicator3'].opacity = 1
        else:
            self.root.ids['time_indicator4'].opacity = 1

        # Set the current day, month, and year in the add workout section
        day, month, year = now.day, now.month, now.year
        self.root.ids.add_workout_screen.ids.month_input.text = str(month)
        self.root.ids.add_workout_screen.ids.day_input.text = str(day)
        self.root.ids.add_workout_screen.ids.year_input.text = str(year)

        # Populate avatar grid
        avatar_grid = self.root.ids['change_avatar_screen'].ids['avatar_grid']
        for root_dir, folders, files in walk("icons/avatars"):
            for f in files:
                img = ImageButton(source="icons/avatars/" + f, on_release=partial(self.change_avatar, f))
                avatar_grid.add_widget(img)

        # Populate workout image grid
        workout_image_grid = self.root.ids['add_workout_screen'].ids['workout_image_grid']
        for root_dir, folders, files in walk("icons/workouts"):
            for f in files:
                img = ImageButton(source="icons/workouts/" + f, on_release=partial(self.update_workout_image, f))
                workout_image_grid.add_widget(img)

        try:
            # Try to read the persisten signin credentials (refresh token)
            with open("refresh_token.txt", "r") as f:
                refresh_token = f.read()

            # use refresh_token to get a new idToken
            self.id_token, self.local_id = self.my_firebase.exchange_refresh_token(refresh_token)

            # Get database data
            result = requests.get(
                "https://fitnessapp-kivy.firebaseio.com/" + self.local_id + ".json?auth=" + self.id_token)
            data = json.loads(result.content.decode())

            # Update avatar image
            avatar_image = self.root.ids['avatar_image']
            avatar_image.source = "icons/avatars/" + data['avatar']

            # Update streak label
            label_streak = self.root.ids['home_screen'].ids['streak_label']

            # Friend List
            self.friends_list = data['friends']

            # Update id label
            self.my_friend_id = data['my_friend_id']
            friend_id_label = self.root.ids['settings_screen'].ids['friend_id_label']
            friend_id_label.text = "ID: " + str(data['my_friend_id'])

            # Get data workouts
            banner_grid = self.root.ids['home_screen'].ids['banner_grid']
            workouts = data['workouts']
            if workouts != "":
                workout_keys = list(workouts.keys())
                streak = helperfunctions.count_workout_streak(workouts)
                if str(streak) == "0":
                    label_streak.text = "[b]0 Hari berturut-turut, latihan sekarang![/b]"
                else:
                    label_streak.text = "[b]" + str(streak) + " Hari berturut-turut[/b]"
                # Sort workouts by date then reverse (we want youngest dates at the start)
                workout_keys.sort(key=lambda value: datetime.strptime(workouts[value]['date'], "%m/%d/%Y"))
                workout_keys = workout_keys[::-1]
                for workout_key in workout_keys:
                    workout = workouts[workout_key]
                    # Populate workout grid in home screen
                    W = WorkoutsBanner(workout_image=workout['workout_image'], description=workout['description'],
                                       type_image=workout['type_image'], number=float(workout['number']),
                                       units=workout['units'],
                                       likes=workout['likes'], date=workout['date'])
                    banner_grid.add_widget(W)

            self.change_screen("home_screen", "none")
        except Exception as e:
            print(e)
            pass

    def add_friend(self, friend_id):
        friend_id = friend_id.replace("\n", "")
        # Make sure friend id was a number otherwise it's invalid
        try:
            int_friend_id = int(friend_id)
        except:
            # Friend id had some letters in it when it should just be a number
            self.show_popup("ID harus berupa angka", "number_only")
            return
        # Make sure they aren't adding themselves
        if friend_id == self.my_friend_id:
            self.show_popup("Maaf, anda tidak dapat menambahkan ID anda sendiri", "own_id")
            return

        # Make sure this is not someone already in their friends list
        if friend_id in self.friends_list.split(","):
            self.show_popup("Teman dengan ID " + friend_id + " sudah ada", "duplicated")
            return

        # Query database and make sure friend_id exists
        check_req = requests.get(
            'https://fitnessapp-kivy.firebaseio.com/.json?orderBy="my_friend_id"&equalTo="' + friend_id + '"')
        data = check_req.json()

        if data == {}:
            # If it doesn't, display it doesn't in the message on the add friend screen
            self.show_popup("ID teman tidak ditemukan", "not_found")
        else:
            # Requested friend ID exists
            key = list(data.keys())[0]
            # new_friend_id = data[key]['my_friend_id']

            # Add friend id to friends list and patch new friends list
            if self.friends_list == "":
                self.friends_list += "%s" % friend_id
            else:
                self.friends_list += ",%s" % friend_id
            patch_data = '{"friends": "%s"}' % self.friends_list
            patch_req = requests.patch(
                "https://fitnessapp-kivy.firebaseio.com/" + self.local_id + ".json?auth=" + self.id_token,
                data=patch_data)
            if patch_req.ok == True:
                self.show_popup("Teman dengan ID " + friend_id + " berhasil ditambahkan", "friend_added")
                self.root.ids['add_friend_screen'].ids['add_friend_input'].text = ""
            else:
                self.show_popup("Maaf, ada kesalahan pada sistem", "error_adding")

            # Add new friend banner in friends list screen
            # if friend_id in self.nicknames.keys():
            #     friend_id_text = "[u]" + self.nicknames[friend_id] + "[/u]"
            # else:
            #     friend_id_text = "[u]Friend ID: " + friend_id + "[/u]"
            # friend_banner = FriendBanner(friend_id=friend_id, friend_id_text=friend_id_text)
            # self.root.ids['friends_list_screen'].ids['friends_list_grid'].add_widget(friend_banner)
            # # Inform them they added a friend successfully
            # self.root.ids['add_friend_screen'].ids[
            #     'add_friend_label'].text = "Friend ID %s added successfully." % friend_id

    def change_avatar(self, image, widget_id):
        # Change avatar in app
        avatar_image = self.root.ids['avatar_image']
        avatar_image.source = "icons/avatars/" + image

        # Change avatar in firebase
        my_avatar = '{"avatar": "%s"}' % image
        change_avatar_req = requests.patch(
            "https://fitnessapp-kivy.firebaseio.com/" + self.local_id + ".json?auth=" + self.id_token, data=my_avatar)
        if change_avatar_req.ok == True:
            self.show_popup("Foto profil berhasil di ganti", "avatar_changed")
        else:
            self.show_popup("Maaf, ada kesalahan pada sistem", "error_change_avatar")

    def update_workout_image(self, filename, widget_id):
        self.workout_image = filename

    def add_workout(self):
        # Get data from all fields in add workout screen
        workout_ids = self.root.ids['add_workout_screen'].ids
        description_input = workout_ids['description_input'].text
        quantity_input = workout_ids['quantity_input'].text
        units_input = workout_ids['units_input'].text
        day_input = workout_ids['day_input'].text
        month_input = workout_ids['month_input'].text
        year_input = workout_ids['year_input'].text
        if self.workout_image == None:
            self.show_popup("Silahkan pilih gambar latihan!", "workout_image_none")
        elif self.option_choice == None:
            self.show_popup("Silahkan pilih jenis perhitungan!", "no_option_choice")
            workout_ids['time_label'].color = (1, 0, 0, 1)
            workout_ids['distance_label'].color = (1, 0, 0, 1)
            workout_ids['sets_label'].color = (1, 0, 0, 1)
        elif quantity_input == "":
            self.show_popup("Silahkan isi jumlah!", "quantity_none")
            workout_ids['quantity_input'].background_color = (1, 0, 0, 1)
        elif quantity_input != "":
            try:
                int_quantity = float(quantity_input)
                if units_input == "":
                    self.show_popup("Silahkan isi satuan!", "units_none")
                    workout_ids['units_input'].background_color = (1, 0, 0, 1)
                elif day_input == "":
                    self.show_popup("Silahkan isi hari!", "day_none")
                    workout_ids['day_input'].background_color = (1, 0, 0, 1)
                elif day_input != "":
                    try:
                        int_day = int(day_input)
                        if month_input == "":
                            self.show_popup("Silahkan isi bulan!", "month_none")
                            workout_ids['month_input'].background_color = (1, 0, 0, 1)
                        elif month_input != "":
                            try:
                                int_month = int(month_input)
                                if year_input == "":
                                    self.show_popup("Silahkan isi tahun!", "year_none")
                                    workout_ids['year_input'].background_color = (1, 0, 0, 1)
                                elif year_input != "":
                                    try:
                                        int_year = int(year_input)
                                        workout_payload = {"workout_image": self.workout_image,
                                                           "description": description_input, "likes": 0,
                                                           "number": int_quantity, "type_image": self.option_choice,
                                                           "units": units_input,
                                                           "date": month_input + "/" + day_input + "/" + year_input}
                                        workout_request = requests.post(
                                            "https://fitnessapp-kivy.firebaseio.com/" + self.local_id + "/workouts.json?auth=" + self.id_token,
                                            data=json.dumps(workout_payload))
                                        # Add the workout to the banner grid in the home screen
                                        banner_grid = self.root.ids['home_screen'].ids['banner_grid']
                                        W = WorkoutsBanner(workout_image=self.workout_image,
                                                           description=description_input,
                                                           type_image=self.option_choice, number=float(quantity_input),
                                                           units=units_input,
                                                           likes="0",
                                                           date=month_input + "/" + day_input + "/" + year_input)
                                        banner_grid.add_widget(W, index=len(banner_grid.children))

                                        # Check if the new workout has made their streak increase
                                        streak_label = self.root.ids['home_screen'].ids['streak_label']
                                        result = requests.get(
                                            "https://fitnessapp-kivy.firebaseio.com/" + self.local_id + ".json?auth=" + self.id_token)
                                        data = json.loads(result.content.decode())
                                        workouts = data['workouts']
                                        streak = helperfunctions.count_workout_streak(workouts)
                                        if str(streak) == "0":
                                            streak_label.text = "[b]0 Hari berturut-turut, latihan sekarang![/b]"
                                        else:
                                            streak_label.text = "[b]" + str(streak) + " Hari berturut-turut[/b]"

                                        self.show_popup("Berhasil menambah data latihan", "workout_added")
                                    except:
                                        self.show_popup("Tahun harus berupa angka!", "year_not_int")
                                        workout_ids['year_input'].background_color = (1, 0, 0, 1)
                                        return
                            except:
                                self.show_popup("Bulan harus berupa angka!", "month_not_int")
                                workout_ids['month_input'].background_color = (1, 0, 0, 1)
                                return
                    except:
                        self.show_popup("Hari harus berupa angka!", "day_not_int")
                        workout_ids['day_input'].background_color = (1, 0, 0, 1)
                        return
            except:
                self.show_popup("Jumlah harus berupa angka!", "quantity_not_int")
                workout_ids['quantity_input'].background_color = (1, 0, 0, 1)
                return

    def change_screen(self, screen_name, transition):
        screen_manager = self.root.ids['screen_manager']

        # Transition
        if transition == "wipe":
            screen_manager.transition = WipeTransition()
        elif transition == "swap":
            screen_manager.transition = SwapTransition()
        elif transition == "slide":
            screen_manager.transition = SlideTransition()
        elif transition == "none":
            screen_manager.transition = NoTransition()
        elif transition == "card":
            screen_manager.transition = CardTransition()

        screen_manager.current = screen_name

    def show_popup(self, message, status):
        self.popup_message = message

        show = Popups()

        self.status_popup = status

        self.popupWindow = Popup(title="Perhatian !", content=show,
                                 size_hint=(None, None), size=(200, 200), auto_dismiss=False)
        self.popupWindow.open()

        self.popup_message = ""

    def dismiss_popup(self):
        if self.status_popup == "registered":
            self.popupWindow.dismiss()
            self.change_screen("login_screen", "wipe")

            self.root.ids["login_screen"].ids["login_email"].text = ""
            self.root.ids["login_screen"].ids["login_password"].text = ""
            self.root.ids["register_screen"].ids["register_email"].text = ""
            self.root.ids["register_screen"].ids["register_password"].text = ""
        elif self.status_popup == "avatar_changed":
            self.popupWindow.dismiss()
            self.change_screen("settings_screen", "swap")

            self.root.ids["login_screen"].ids["login_email"].text = ""
            self.root.ids["login_screen"].ids["login_password"].text = ""
            self.root.ids["register_screen"].ids["register_email"].text = ""
            self.root.ids["register_screen"].ids["register_password"].text = ""
        elif self.status_popup == "workout_added":
            self.popupWindow.dismiss()
            self.change_screen("home_screen", "card")

            self.root.ids["login_screen"].ids["login_email"].text = ""
            self.root.ids["login_screen"].ids["login_password"].text = ""
            self.root.ids["register_screen"].ids["register_email"].text = ""
            self.root.ids["register_screen"].ids["register_password"].text = ""
        else:
            self.popupWindow.dismiss()

        self.status_popup = ""

    def logout(self):
        with open("refresh_token.txt", "w") as f:
            f.write("")

        avatar_image = self.root.ids['avatar_image']
        avatar_image.source = "icons/avatars/man.png"

        self.change_screen("login_screen", "wipe")


if __name__ == '__main__':
    MainApp().run()
