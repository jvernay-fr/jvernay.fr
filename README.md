# jvernay.fr website sources

This is the source code for deploying the `jvernay.fr` website.
Its requirements are **Python 3** and PIP's **requests** library.

Do not forget to pull git submodules by doing:
```sh
git clone https://github.com/jvernay-fr/jvernay.fr.git --recurse-submodules
```

```sh
python3 -m pip install requests
python3 -m jvernayfr-py --deploy
```

Although it is not meant to be portable, it should be easy to take
the sources from the `jvernayfr-py` folder and adapt `__main__.py` to
other projects.
