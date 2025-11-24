
# Robus — prototyp robota kelnera

Robus („kerfus”) to wczesny prototyp robota jeżdżącego z tacą. Projekt ma docelowo stać się modularną platformą robotyczną, ale obecna wersja skupia się na jednej funkcji — prostym kelnerze, który potrafi poruszać się autonomicznie i przewozić niewielkie przedmioty.

Robot wykorzystuje kamerę oraz lekki moduł AI, który analizuje obraz i generuje podstawowe komendy ruchu (np. skręć, jedź prosto, zatrzymaj się). Jest to minimalna baza pod kolejne iteracje.


## Zespół i Role

- [@Wiktor Wilk](https://github.com/wiktorw95) - **Project Lead**  
  Zarządza repozytorium, nadaje uprawnienia członkom zespołu i koordynuje pracę. Odpowiada za zatwierdzanie finalnych Pull Requestów.

- [@Amelia Mańkowska](https://www.github.com/pjatk-S31320) - **Reviewer**  
  Przegląda Pull Requesty, weryfikuje jakość kodu i dba o zgodność z wytycznymi projektu. Pomaga w rozwiązywaniu konfliktów merge.

- [@PaweL Madej](https://www.github.com/RussianDancer123) - **Contributor**  
  Pisze kod, zgłasza Pull Requesty i implementuje funkcjonalności zgodnie z wymaganiami. Dba o testy jednostkowe i dokumentację kodu.

- [@Jakub Grzenia](https://github.com/PjwstkJestSuper) - **Issue Manager**  
  Zarządza zgłoszeniami (issues), klasyfikuje je i przypisuje do odpowiednich osób. Śledzi postęp prac i raportuje status projektu.



## Dokumentacja

Celem tego projektu jest stworzenie lekkiej, taniej platformy mobilnej, która będzie mogła poruszać się autonomicznie, wykorzystując wizję komputerową do nawigacji. Platforma będzie także modułowa, co umożliwi wymianę komponentów (np. tacek, uchwytów, koszyków) w zależności od potrzeb. Wersja początkowa skoncentruje się na stabilności ruchu i podstawowym unikaniu przeszkód, a w przyszłości planowane są zaawansowane funkcje, takie jak mapowanie przestrzeni i pełna autonomia.

### Plan Rozwoju

- Stabilizacja ruchu i nawigacji  
- Podstawowe unikanie przeszkód  
- Początkowy system komend AI  
- Rozpoznawanie obiektów (np. stolików)  
- Wymienne moduły: tacki, uchwyty, koszyki  
- Proste planowanie tras, np. "od stolika A do stolika B"  
- Podstawowy SLAM (Simultaniczne Lokalizowanie i Mapowanie)  
- Zaawansowane planowanie tras i podejmowanie decyzji  
- Pełna autonomia w różnych środowiskach  

## Struktura
```plaintext
robus/
  ├── docs/
  ├── AI/
  ├── IoT/
  ├── models/
  └── README.md
```

<p align="center"> <img src="docs/logo.png" alt="Robus Logo"> </p>

