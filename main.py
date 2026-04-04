import random
from collectins import defaultdict
train_text="""
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
markov_model =defaultdict(lambda:defaultdict(int))
words =train_text.split()
#construirea modelului Markov
for i in  range (len(words)-1):
    current_word=words[i]
    next_word=words[i+1]
    markov_model[current_word][next_word]+=1
#functia de generare a textului def generate_text(model,length=20);
current_word=random.choice(list(model.keys()))
generated_words=[current_word]
for_in range (lenght)next_words=
model[current_word]
if not next_words:
    break
next_wor=random.choices(list(next_words.keys()),weights=listst(next_words.values())
                        k=1)[0]
generated_words.append(next_words)
current word=next_word return