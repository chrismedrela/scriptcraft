=======================
Co to jest Scriptcraft?
=======================

Scriptcraft jest grą polegającą na zaprogramowaniu własnych jednostek
(bazy, zbieraczy minerałów i czołgów) tak, aby pokonać innych
graczy. Internetowy wieloosobowy (MMORTS!) pierwowzór dostępny jest
pod adresem http://informatyka.wroc.pl/scriptcraft, natomiast **ten
projekt jest** jego **klonem, dzięki któremu można uruchomić
Scriptcraft'a na własnym komputerze**. W ten sposób można szybko
przetestować programy swoich jednostek, zanim zmierzą się one z
prawdziwymi graczami w internetowej wersji Scriptcraft'a!

==========
Możliwości
==========

W chwili obecnej Scriptcraft jest we wczesnym stadium rozwoju, dlatego
udostępnia on najbardziej podstawowe funkcje i możliwości.

- Dostępna jest jedna mapa o rozmiarze 64x64.
- Gry można zapisywać i wczytywać.
- Programy można pisać w następujących językach: ``python``, ``c++``;
  ponadto istnieje tzw. ``star-program``, który wykonuje polecenia
  wysyłane przez inną jednostkę. Programy **nie są** uruchamiane w
  wyizolowanym środowisku ani nie są killowane w przypadku zbyt
  długiego czasu działania.
- Można wysyłać zapytania systemowe (zobacz `dokumentację gry`_) oraz
  wiadomości między jednostkami.
- Wszystkie polecenia wydawane jednostkom przez Twoje programy są
  interpretowane tak samo jak w wersji internetowej **z wyjątkiem**
  polecenia ``PROGRAM``, które w chwili obecnej nie jest
  zaimplementowane. W zamian za to nowo produkowane jednostki
  otrzymują taki sam program jaki ma baza.

.. _`dokumentację gry`: http://informatyka.wroc.pl/node/714

Scriptcraft działa pod Pythonem 2.6 i 2.7 pod Linuxem. Planowana jest
obsługa także systemu Windows.

==========
Screenshot
==========

.. image:: https://github.com/krzysiumed/scriptcraft/raw/experimental/screenshot.png
   :alt: Screenshot not available.
   :align: center

==========
Instalacja
==========

Scriptcraft można zainstalować na dwa sposoby. Prostszy sposób polega
na wpisaniu w bashu:

  sudo pip install scriptcraft

Drugim sposobem jest pobranie źródeł z `pypi`_ lub z `githuba`_. Po
ściągnięciu i rozpakowaniu paczki należy wpisać w bashu:

  sudo python setup.py install

.. _`pypi`: http://pypi.python.org/pypi/scriptcraft/
.. _`githuba`: https://github.com/krzysiumed/scriptcraft

============
Uruchomienie
============
Aby uruchomić grę, w bashu należy wpisać:

  scriptcraft

Po pojawieniu się okna gry należy utworzyć grę wybierając z menu
``Game`` opcję ``New game``. Następnie należy dodać graczy (opcja
``Add player``) wybierając dla każdego jego nazwę i kolor. Każdy gracz
otrzymuje na starcie cztery zbieracze minerałów i bazę w okolicach
złóż minerałów.

Mapę można przesuwać przytrzymując lewy przycisk myszy. Rolka myszy
służy do powiększania i pomniejszania widoku. Pojedyncze kliknięcie
lewym przyciskiem myszy służy do zaznaczania pól mapy. Po takim
kliknięciu w konsoli pojawią się szczegółowe informacje dotyczące
zaznaczonego pola i jednostki na tym polu, jeżeli taka istnieje.

Jednostkom można ustawiać (lub usuwać) programy (opcje ``Set program``
i ``Set star-program`` oraz ``Delete program``). Po wybraniu opcji
``Set program`` należy wskazać plik zawierający kod źródłowy
programu. Plik powininen mieć odpowiednie rozszerzenie (``.py`` dla
pythona, ``.cpp`` dla c++). Aby móc programować jednostki w języku C++,
potrzebny jest kompilator ``g++``.

W celu zasymulowania jednej tury gry, należy wybrać opcję ``One turn
in game`` lub nacisnąć na klawiaturze literę ``t``. Okno gry może być
przez kilka chwil nieaktywne.

Aby zapoznać się ze sposobem, w jaki powinny działać programy, proszę
zajrzeć do materiałów internetowej wersji Scriptcrafta: `tutoriala`_ i
`dokumentacji`_.

.. _`tutoriala`: http://informatyka.wroc.pl/node/622
.. _`dokumentacji`: http://informatyka.wroc.pl/node/714
