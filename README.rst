=======================
Co to jest Scriptcraft?
=======================

Scriptcraft jest grą polegającą na zaprogramowaniu własnych jednostek
(zbieraczy minerałów, czołgów i budujących je baz) tak, aby pokonać innych
graczy. Internetowy wieloosobowy (MMORTS!) pierwowzór dostępny jest pod
adresem http://informatyka.wroc.pl/scriptcraft, natomiast **ten projekt jest**
jego **klonem, dzięki któremu można uruchomić Scriptcrafta na własnym
komputerze**. W ten sposób można szybko przetestować programy swoich
jednostek, zanim zmierzą się one z prawdziwymi graczami w internetowej wersji
Scriptcrafta!

.. image:: https://github.com/chrismedrela/scriptcraft/raw/experimental/screenshot.png
   :alt: Zdjęcie niedostępne.
   :align: center

==========
Możliwości
==========

Na razie Scriptcraft udostępnia podstawowe funkcje i możliwości:

- Zaimplementowana jest taka sama funkcjonalność jak w internetowej wersji --
  można wysyłać wiadomości między jednostkami oraz tzw. zapytania systemowe
  (zobacz `dokumentację gry`_). Wszystkie polecenia wydawane jednostkom przez
  Twoje programy są interpretowane tak samo **z wyjątkiem** polecenia
  ``PROGRAM``, które w chwili obecnej nie jest zaimplementowane. W zamian za
  to nowo produkowane jednostki otrzymują taki sam program jaki ma baza.
- Dostępna jest jedna mapa (taka sama jak na tzw. `szybkim świecie`_) o
  rozmiarze 64x64.
- Programy można pisać w następujących językach: ``python``, ``c++`` (dodanie
  kolejnych nie jest problemem, jeśli jesteś zainteresowany -- pisz); ponadto
  istnieje tzw. star-program, który wykonuje polecenia wysyłane przez inną
  jednostkę. Do wyboru jest także "język" ``output`` służący do bezpośredniego
  wydawania komend. Programy są zabijane w przypadku przekroczenia limitu
  czasu, ale **nie** są uruchamiane w wyizolowanym środowisku.
- Polecenia można wydawać także przy pomocy myszki.
- Gry można zapisywać i wczytywać.
- Mapy są zapisywane w formacie tekstowym i można łatwo samemu stworzyć swoją
  mapę.

.. _`dokumentację gry`: http://informatyka.wroc.pl/node/714
.. _`szybkim świecie`: http://informatyka.wroc.pl/node/722

Dostępna jest skompilowana wersja pod Windowsa -- instalacja Pythona nie jest
konieczna. Scriptcraft można zainstalować także ze źródeł (wymagany Python 2.6
lub 2.7, system Windows lub Linux).

==========
Instalacja
==========

Instalacja pod Windowsem
------------------------

Ściągnij `to archiwum zip`_ i rozpakuj. Gotowe!

.. _`to archiwum zip`: https://github.com/chrismedrela/scriptcraft/raw/windows-dist/scriptcraft-for-windows.zip

Instalacja ze źródeł
--------------------

Potrzebujesz Pythona w wersji 2.6 lub 2.7 (ale nie 3.x!) z zainstalowanym
`PIL`_ oraz ``tcl/tk``. Pod Ubuntu wystarczy wpisać w shellu:

::

  sudo apt-get install python-imaging-tk tk8.5 tk8.5-dev tcl8.5 tcl8.5-dev python-tk
  sudo pip install PIL

Potrzebujesz także kod źródłowy z `githuba`_.

::

  git clone https://github.com/chrismedrela/scriptcraft.git

.. _`githuba`: https://github.com/chrismedrela/scriptcraft
.. _`PIL`: http://www.pythonware.com/products/pil/

=================
Krótki przewodnik
=================

Konfiguracja i uruchomienie
---------------------------

Scriptcraft do kompilacji i wykonywania programów korzysta z zewnętrznych
programów takich jak np. kompilator ``g++``. Aby móc programować w danym
języku, musisz wskazać jakie polecenia mają być wykonane, aby skompilować i
wykonać program w danym języku. W szczególności, aplikacja gry musi wiedzieć,
gdzie znajduje się kompilator.

Pod Linuxem wystarczy sprawdzić w bashu, czy komendy ``g++`` oraz ``python``
są rozpoznawane, a jeśli nie są, to shell podpowie Ci, jakie pakiety musisz
doinstalować. Pamiętaj, że nie jest to wymagane, jeżeli nie zamierzasz
programować w danym języku.

Pod Windowsem otwórz plik konfiguracji ``configuration.ini`` znajdujący się w
głównym katalogu gry. Jest on podzielony na sekcje i każda z nich z wyjątkiem
sekcji ``DEFAULT`` odpowiada jednemu językowi. W każdej sekcji języka, w
którym zamierzasz programować, musisz zmienić wiersze rozpoczynające się od
``compile`` i ``execute`` oznaczające kolejno: polecenie kompilacji i
wykonania.

Na przykład, jeżeli chcesz programować w ``C++``, musisz znaleźć
kompilator. Jeżeli korzystasz z jakiegoś środowiska programistycznego
(np. `DevCpp`_), to powinieneś już go mieć. Musisz znaleźć aplikację o nazwie
``g++.exe``. Jeżeli posiadasz DevCpp zainstalowany w folderze ``C:\DevCpp``,
to ścieżka do kompilatora to ``C:\DevCpp\bin\g++.exe``. W takim przypadku
sekcja ``CPP`` pliku ``configuration.ini`` mogłaby wyglądać tak::

  [CPP]
  sourceextension = cpp
  binaryextension = exe
  compile = "C:\DevCpp\bin\g++.exe" src.cpp -o bin.exe
  execute = bin.exe


Jeżeli zamierzasz programować w Pythonie, sprawdź czy masz go
zainstalowanego. Na dysku ``C:`` poszukaj folderu o nazwie rozpoczynającej się
od ``Python`` i zakończonej dwoma cyframi, np. ``Python26``. Interpreter
Pythona znajduje się wewnątrz tego katalogu i jest nazwany
``Python.exe``. Jeżeli nie masz jeszcze zainstalowanego Pythona, ściągnij
instalator `stąd`_. Przykładowa sekcja ``PYTHON`` pliku konfiguracji mogłaby
wyglądać tak::

  [PYTHON]
  sourceextension = py
  binaryextension = py
  compile = copy src.py bin.py
  execute = "C:\Python26\Python.exe" bin.py

.. _`stąd`: http://www.python.org/getit/

Po dokonaniu zmian pamiętaj o zapisaniu pliku. Teraz możesz już uruchomić
grę. Pod Windowsem musisz dwukrotnie kliknąć na ikonę pliku
"scriptcraft.exe". Jeżeli ściągnąłeś źródła, przejdź do folderu z grą i wpisz
w bashu::

  python runclient.py

.. _`DevCpp`: http://www.bloodshed.net/devcpp.html

Interfejs gry
-------------

Po pojawieniu się pustego okna gry tworzymy nową grę wybierając z menu ``Gra``
opcję ``Nowa gra`` lub używając skrótu ``Ctrl+n``. Następnie należy dodać
graczy (opcja ``Dodaj gracza``). Każdy gracz otrzymuje na początku bazę z
pewną ilością zmagazynowanych minerałów oraz cztery zbieracze minerałów w
okolicach złóż minerałów.

Mapę można przesuwać przytrzymując lewy przycisk myszy. Rolka myszy służy do
powiększania i pomniejszania. Pojedyncze kliknięcie lewym przyciskiem myszy
służy do zaznaczania jednostek. Zaznaczonej jednostce można wydać komendę
ruchu (wokół wskazanego pola pojawia się wtedy zielony pierścień), ataku
(czerwony pierścień) lub zbierania minerałów (granatowy pierścień) poprzez
kliknięcie prawym klawiszem myszy na dowolnym polu mapy. Podwójne kliknięcie
lewym przyciskiem myszy otworzy nowe okno, gdzie można edytować kod programu
klikniętej jednostki oraz sprawdzić wynik jego kompilacji i wykonywania.

W celu uruchomienia gry, musisz wybrać opcję ``Symuluj jedną turę
gry`` lub nacisnąć na klawiaturze przycisk ``t``. Możliwe jest obserwowanie
przebiegu gry "w czasie rzeczywistym", tzn. symulując kolejne tury gry jedna
za drugą poprzez wybranie opcji ``Symulacja gry w pętli`` lub naciśnięcie
spacji.

Programowanie jednostek
-----------------------

Aby zaprogramować jednostkę, kliknij na nią dwukrotnie, a w otwartym oknie
wybierz język programowania oraz wpisz kod. Zamknij okno, zasymuluj jedną
turę gry i otwórz okno z powrotem aby sprawdzić, czy program został
skompilowany oraz co wyrzucił na wyjście. Zamiast otwierać okno możesz wskazać
jednostkę myszką i sprawdzić, jaka komenda została wydana obserwując tekst w
lewym górnym rogu.

Oprócz tego jednostka może: nie mieć programu lub może mieć tzw. "star
program" polegający na odbieraniu wiadomości od innych jednostek i wykonywaniu
zawartych w nich komend. W przypadku wybrania jednej z tych dwóch opcji
zawartość pola tekstowego "Kod" jest ignorowana. Ponadto na liście języków
istnieje opcja ``output`` która wypisuje na wyjście to, co zostałe wpisane
jako kod programu. Pozwala to na bezpośrednie wpisanie komend do wykonania.

Twój program otrzymuje na wejściu informacje dotyczące sterowanej przez niego
jednostki, jej otoczenia oraz wysłane do niej wiadomości. Na wyjściu programu
powinna znaleźć się komenda oraz ewentualnie wiadomości do wysłania. Wejście
oraz sposób interpretacji wyjścia są dokładnie takie same jak w internetowej
wersji (z wyjątkiem komendy ``PROGRAM``, która obecnie nie jest
zaimplementowana) i są opisane w `dokumentacji internetowej wersji
Scriptcrafta`_.

.. _`dokumentacji internetowej wersji Scriptcrafta`: http://informatyka.wroc.pl/node/714

===
FAQ
===

1. Mam problemy z instalacją lub konfiguracją. / Aplikacja eksplodowała w
   powietrze. / Znalazłem błąd! / Pod Windowsem po dwukrotnym kliknięciu na
   ikonę gry nic się nie dzieje.

     Jeżeli tylko masz czas i chęć, zgłoś ten problem do mnie. Pozwoli mi to
     na ulepszenie aplikacji. Jeżeli problem nie dotyczy instalacji ani
     konfiguracji, postaraj się wysłać mi także logi gry (plik
     ``.scriptcraft`` oraz pod Windowsem ``scriptcraft.exe.log``).

     Skontaktować się ze mną możesz na `polskim forum Pythona`_, na `forum
     Wrocławskiego Portalu Informatycznego`_ lub mailowo (mój adres to
     ``chris.medrela+scriptcraft [zwierzątko] gmail.com``).

.. _`polskim forum Pythona`: http://pl.python.org/forum/index.php?topic=2959.0
.. _`forum Wrocławskiego Portalu Informatycznego`: http://informatyka.wroc.pl/forum/viewtopic.php?f=67&t=1347

2. Czy istnieje tutorial wprowadzający w świat Scriptcrafta?

     Tak, na potrzeby internetowej wersji zostało opracowane `to krótkie
     wprowadzenie`_.

.. _`to krótkie wprowadzenie`: http://informatyka.wroc.pl/node/622
