# STENO

### SET UP

```
pip install -r requirements.txt
```

### GENERATE KEYS

```
python generate_keys.py
```

### Audio

- Encode
```
python cli.py hide audio examples/audio.wav hide.txt mypublickey.pem examples/audio-secret.wav
```

- Decode
```
python cli.py extract audio examples/audio-secret.wav myprivatekey.pem your_passphrase hide_extracted.txt
```

### Image

- Encode
```
python cli.py hide image examples/image.png hide.txt mypublickey.pem examples/image-secret.png
```

- Decode
```
python cli.py extract image examples/image-secret.png myprivatekey.pem your_passphrase hide_extracted.txt
```