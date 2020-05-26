import requests
import json
from kivy.app import App


class MyFirebase():
    wak = "AIzaSyAH9mw6D0ghi149iu32asp296L9R9LUI3Q"  # Web Api Key

    def sign_up(self, email, password):
        app = App.get_running_app()
        email = email.replace("\n", "")
        password = password.replace("\n", "")
        signup_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key=" + self.wak
        signup_payload = {"email": email, "password": password, "returnSecureToken": True}
        sign_up_request = requests.post(signup_url, data=signup_payload)
        sign_up_data = json.loads(sign_up_request.content.decode())
        # print(sign_up_request.ok)
        # print(sign_up_request.content.decode())
        if sign_up_request.ok == False:
            error_message = sign_up_data["error"]['message']
            if error_message == "EMAIL_EXISTS":
                app.show_popup("Email sudah terdaftar!", "error_message")
            elif error_message == "MISSING_PASSWORD":
                app.show_popup("Silahkan isi password anda!", "error_message")
            elif error_message == "MISSING_EMAIL":
                app.show_popup("Silahkan isi email anda!", "error_message")
            elif error_message == "INVALID_EMAIL":
                app.show_popup("Mohon isi email dengan format yang benar!", "error_message")
            elif error_message == "WEAK_PASSWORD : Password should be at least 6 characters":
                app.show_popup("Password minimal harus 6 karakter", "error_message")
        elif sign_up_request.ok == True:
            localId = sign_up_data["localId"]
            idToken = sign_up_data["idToken"]

            # request my friend id from firebase
            friend_get_req = requests.get("https://fitnessapp-kivy.firebaseio.com/next_friend_id.json?auth=" + idToken)
            my_friend_id = friend_get_req.json()

            # post data to firebase
            my_data = '{"avatar": "man-1.png", "friends": "", "streak": 0, "workouts": "", "my_friend_id": "%s"}' % my_friend_id
            post_request = requests.patch("https://fitnessapp-kivy.firebaseio.com/" + localId + ".json?auth=" + idToken,
                                          data=my_data)
            if post_request.ok == True:
                next_id = my_friend_id + 1
                data_next_id = '{"next_friend_id": %s}' % next_id
                update_next_friend_id = requests.patch(
                    "https://fitnessapp-kivy.firebaseio.com/.json?auth=" + idToken, data=data_next_id)
                if update_next_friend_id.ok == True:
                    app.show_popup("Akun anda berhasil di daftarkan, silahkan login.", "registered")
                else:
                    app.show_popup("Maaf, ada kesalahan pada sistem", "error_register")
            else:
                app.show_popup("Maaf, ada kesalahan pada sistem", "error_register")

    def exchange_refresh_token(self, refresh_token):
        refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + self.wak
        refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
        refresh_req = requests.post(refresh_url, data=refresh_payload)
        # print("REFRESH OK?", refresh_req.ok)
        # print(refresh_req.json())
        local_id = refresh_req.json()['user_id']
        id_token = refresh_req.json()['id_token']
        return id_token, local_id

    def sign_in(self, email, password):
        app = App.get_running_app()
        email = email.replace("\n", "")
        password = password.replace("\n", "")
        signin_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + self.wak
        signin_payload = {"email": email, "password": password, "returnSecureToken": True}
        sign_in_request = requests.post(signin_url, data=signin_payload)
        sign_in_data = json.loads(sign_in_request.content.decode())
        # print(sign_in_request.ok)
        # print(sign_in_request.content.decode())
        if sign_in_request.ok == False:
            error_message = sign_in_data["error"]['message']
            if error_message == "INVALID_PASSWORD":
                app.show_popup("Password anda salah!", "error_message")
            elif error_message == "EMAIL_NOT_FOUND":
                app.show_popup("Email tidak ditemukan!", "error_message")
            elif error_message == "INVALID_EMAIL":
                app.show_popup("Mohon isi email dengan format yang benar!", "error_message")
        elif sign_in_request.ok == True:
            refreshToken = sign_in_data["refreshToken"]
            localId = sign_in_data["localId"]
            idToken = sign_in_data["idToken"]

            # save refreshToken to a file
            with open("refresh_token.txt", "w") as f:
                f.write(refreshToken)

            # save localId to a variable in main app class
            # save idToken to a variable in main app class
            app.local_id = localId
            app.id_token = idToken

            app.root.ids["login_screen"].ids["login_email"].text = ""
            app.root.ids["login_screen"].ids["login_password"].text = ""
            app.root.ids["register_screen"].ids["register_email"].text = ""
            app.root.ids["register_screen"].ids["register_password"].text = ""

            app.on_start()

    def update_likes(self, friend_id, workout_key, likes, *args):
        app = App.get_running_app()
        friend_patch_data = '{"likes": %s}' % (likes)
        # Get their database entry based on their friend id so we can find their local ID
        check_req = requests.get(
            'https://fitnessapp-kivy.firebaseio.com/.json?orderBy="my_friend_id"&equalTo="' + friend_id + '"')
        data = check_req.json()
        their_local_id = list(data.keys())[0]

        self.update_likes_patch_req = requests.patch(
            "https://fitnessapp-kivy.firebaseio.com/%s/workouts/%s.json?auth=%s" % (
                their_local_id, workout_key, app.id_token), data=friend_patch_data)
        print("https://fitnessapp-kivy.firebaseio.com/%s/workouts/%s.json?auth=%s" % (
        their_local_id, workout_key, app.id_token))
        if self.update_likes_patch_req.ok == True:
            app.show_popup("Anda menyukai latihan teman anda!", "add_like")
        elif self.update_likes_patch_req.ok == False:
            app.show_popup("Maaf, ada kesalahan pada sistem", "error_add_like")
