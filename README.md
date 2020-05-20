# Aplikasi Fitnes menggunakan Kivy

Projek aplikasi mobile menggunakan Python.

## Cara install

### Update Kivy (Jika sudah install)

```
python -m pip uninstall -y kivy.deps.glew kivy.deps.gstreamer kivy.deps.sdl2 kivy.deps.angle
```

### Install Kivy

**1. Pastikan Anda memiliki pip, wheel, dan virtualenv terbaru:**

```
python -m pip install --upgrade pip wheel setuptools virtualenv
```

**2. Instal dependensi**

```
python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*
```
```
python -m pip install kivy_deps.gstreamer==0.1.*
```
```
python -m pip install kivy_deps.angle==0.1.*
```

**3. Install Kivy**

```
python -m pip install kivy==1.11.1
```

>Saya sarankan menggunakan Python 3.7.1 dan Pycharm sebagai editornya