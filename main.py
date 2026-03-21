import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Seguntial
from tensorflow.keras.layers import Ebedding,LSTM,Dense
from tensorflow.keras.prepocessing.text import Tokenizer
from tensorflow.keras.sequences import pad_sequencing
text="""
A fost odată ca-n povești,
A fost ca niciodată,
Din rude mari împărătești,
O prea frumoasă fată.

Și era una la părinți
Și mândră-n toate cele,
Cum e Fecioara între sfinți
Și luna între stele.

Din umbra falnicelor bolți
Ea pasul și-l îndreaptă
Lângă fereastră, unde-n colț
Luceafărul așteaptă.

Privea în zare cum pe mări
Răsare și străluce,
Pe mișcătoarele cărări
Corăbii negre duce.

Îl vede azi, îl vede mâni,
Astfel dorința-i gata;
El iar, privind de săptămâni,
Îi cade dragă fata.

Cum ea pe coate-și răzima
Visând ale ei tâmple
De dorul lui și inima
Și sufletu-i se împle.

Și cât de viu s-aprinde el
În orișicare sară,
Spre umbra negrului castel
Când ea o să-i apară."""