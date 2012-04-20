=======================
Co to jest Scriptcraft?
=======================

Scriptcraft jest grą polegającą na zaprogramowaniu własnych jednostek
(bazy, zbieraczy minerałów i czołgów) tak, aby pokonać innych
graczy. Internetowy wieloosobowy (MMORTS!) pierwowzór dostępny jest
pod adresem http://informatyka.wroc.pl/scriptcraft, natomiast **ten
projekt jest** jego **klonem, dzięki któremu możesz uruchomić
Scriptcraft'a na własnym komputerze**. W ten sposób możesz szybko
przetestować programy Twoich jednostek, zanim zmierzą się one z
prawdziwymi graczami w internetowej wersji Scriptcraft'a.

==========
Możliwości
==========

W chwili obecnej Scriptcraft jest we wczesnym stadium rozwoju, dlatego
udostępnia on najbardziej podstawowe funkcje i możliwości.

- Dostępna jest jedna mapa o rozmiarze 64x64.
- Gry można zapisywać i wczytywać.
- Programy można pisać w następujących językach: ``python``, ``c++``;
  ponadto istnieje tzw. ``star-program``, który wykonuje polecenia
  wysyłane przez inną jednostkę.
- Można wysyłać zapytania systemowe (zobacz `dokumentację gry`_) oraz
  wiadomości między jednostkami.
- Wszystkie polecenia wydawane jednostkom przez Twoje programy są
  interpretowane tak samo jak w wersji internetowej **z wyjątkiem**
  polecenia ``PROGRAM``, które w chwili obecnej nie jest
  zaimplementowane.

.. _`dokumentację gry`: http://informatyka.wroc.pl/node/714

Scriptcraft działa pod Pythonem 2.6 i 2.7 pod Windowsem i Linuxem. Nie
był testowany pod innymi systemami operacyjnymi, ale jest całkiem
prawdopodobne, że zadziała.

==========
Instalacja
==========

Scriptcraft można ściągnąć z `pypi`_

.. _`pypi`: http://pypi.python.org/pypi/scriptcraft/

-------------------------
Instalacja pod Windowsem.
-------------------------

Ściągnij z pypi wersję odpowiadającą zainstalowanej u Ciebie wersji
Pythona, a następnie kliknij dwukrotnie na ściągniętym pliku .exe i
postępuj zgodnie z krokami instalacji.

Jaką wersję Pythona mam zainstalowaną?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python powinien być u Ciebie zainstalowany w folderze ``C:\Python26``
lub ``C:\Python27`` w zależności od posiadanej przez Ciebie wersji:
odpowiednio 2.6 i 2.7. Jeżeli nie masz na dysku ``C:`` żadnego folderu
o podobnej nazwie, to znaczy, że musisz zainstalować `Pythona`_
(najlepiej najnowszą wersję z gałęzi 2.7.x, w chwili obecnej jest to
2.7.3). Jeżeli posiadasz folder o podobnej nazwie
(np. ``C:\Python30``), to znaczy że masz zainstalowanego Pythona, ale
w wersji, z którą Scriptcraft może nie działać. Dlatego w takim
przypadku również zalecane jest zainstalowanie Pythona 2.7.x.

.. _`Pythona`: http://www.python.org/download/

-------------------------------------------------
Instalacja ze źródeł (dowolny system operacyjny).
-------------------------------------------------
Pobieramy z pypi wersję z kodem źródłowym i rozpakowujemy. Następnie
należy uruchomić plik ``setup.py`` z argumentem ``install`` - pod Linuxem
trzeba wpisać w bashu:

  sudo python setup.py install

natomiast pod Windowsem:

  C:\\Python2x\\python.exe setup.py install

gdzie zamiast ``Python2x`` należy wpisać ``Python26`` lub ``Python27`` w
zależności od tego, którą wersję Pythona posiadasz.


