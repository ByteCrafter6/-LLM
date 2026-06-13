"""
AI Cititor de Texte - Sistem complet de la zero
================================================
Model: TF-IDF + Cosine Similarity (fara API extern)
Baza de date: SQLite (locala, persistenta)
Suport: fisiere .txt si .pdf
Limba: Romana
"""

import os
import re
import math
import sqlite3
import pickle
import string
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime


# ─────────────────────────────────────────────
#  CONSTANTE
# ─────────────────────────────────────────────
DB_PATH = "knowledge_base.db"
MODEL_PATH = "model.pkl"
CHUNK_SIZE = 3000        # cuvinte per fragment
CHUNK_OVERLAP = 50      # suprapunere intre fragmente
TOP_K = 3               # cele mai relevante fragmente returnate

STOPWORDS_RO = {
    "și", "sau", "dar", "că", "nu", "se", "la", "în", "pe", "de", "cu",
    "din", "prin", "pentru", "care", "este", "sunt", "era", "au", "am",
    "ai", "el", "ea", "ei", "ele", "noi", "voi", "eu", "tu", "un", "o",
    "al", "ale", "cel", "cea", "cei", "cele", "tot", "toți", "toate",
    "mai", "ca", "să", "fie", "fost", "avea", "acest", "această", "acești",
    "aceste", "după", "înainte", "când", "cum", "unde", "dacă", "deci",
    "astfel", "însă", "totuși", "iar", "chiar", "foarte", "acum", "atunci",
    "apoi", "deja", "doar", "până", "între", "despre", "spre", "sub",
    "peste", "fără", "contra", "dintre", "printre", "asupra", "întrucât",
}


# ─────────────────────────────────────────────
#  BAZA DE DATE
# ─────────────────────────────────────────────
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init()

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nume TEXT NOT NULL,
                    cale TEXT,
                    continut TEXT NOT NULL,
                    nr_cuvinte INTEGER,
                    adaugat_la TEXT
                );

                CREATE TABLE IF NOT EXISTS fragmente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    pozitie INTEGER,
                    FOREIGN KEY (document_id) REFERENCES documente(id)
                );

                CREATE TABLE IF NOT EXISTS model_meta (
                    cheie TEXT PRIMARY KEY,
                    valoare TEXT
                );
            """)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def salveaza_document(self, nume: str, continut: str, cale: str = "") -> int:
        nr_cuvinte = len(continut.split())
        adaugat_la = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO documente (nume, cale, continut, nr_cuvinte, adaugat_la) VALUES (?,?,?,?,?)",
                (nume, cale, continut, nr_cuvinte, adaugat_la)
            )
            return cur.lastrowid

    def salveaza_fragmente(self, document_id: int, fragmente: list[str]):
        with self._conn() as conn:
            conn.executemany(
                "INSERT INTO fragmente (document_id, text, pozitie) VALUES (?,?,?)",
                [(document_id, f, i) for i, f in enumerate(fragmente)]
            )

    def get_toate_fragmente(self) -> list[tuple]:
        with self._conn() as conn:
            return conn.execute(
                "SELECT f.id, f.text, d.nume FROM fragmente f JOIN documente d ON f.document_id=d.id"
            ).fetchall()

    def get_documente(self) -> list[tuple]:
        with self._conn() as conn:
            return conn.execute(
                "SELECT id, nume, nr_cuvinte, adaugat_la FROM documente ORDER BY adaugat_la DESC"
            ).fetchall()

    def document_exista(self, nume: str) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT id FROM documente WHERE nume=?", (nume,)).fetchone()
            return row is not None

    def sterge_document(self, doc_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM fragmente WHERE document_id=?", (doc_id,))
            conn.execute("DELETE FROM documente WHERE id=?", (doc_id,))

    def nr_documente(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM documente").fetchone()[0]

    def nr_fragmente(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM fragmente").fetchone()[0]


# ─────────────────────────────────────────────
#  PROCESARE TEXT
# ─────────────────────────────────────────────
class Procesor:
    @staticmethod
    def curata(text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:\-()]', ' ', text)
        return text.strip()

    @staticmethod
    def tokenizeaza(text: str) -> list[str]:
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Inlocuieste diacritice pentru matching mai bun
        for src, dst in [('ă','a'),('â','a'),('î','i'),('ș','s'),('ț','t'),
                         ('Ă','a'),('Â','a'),('Î','i'),('Ș','s'),('Ț','t')]:
            text = text.replace(src, dst)
        tokens = text.split()
        return [t for t in tokens if t not in STOPWORDS_RO and len(t) > 2]

    @staticmethod
    def fragmenteaza(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        cuvinte = text.split()
        fragmente = []
        i = 0
        while i < len(cuvinte):
            fragment = ' '.join(cuvinte[i:i + size])
            fragmente.append(fragment)
            i += size - overlap
        return fragmente

    @staticmethod
    def citeste_fisier(cale: str) -> str:
        ext = Path(cale).suffix.lower()
        if ext == '.txt':
            with open(cale, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(cale) as pdf:
                    return '\n'.join(p.extract_text() or '' for p in pdf.pages)
            except ImportError:
                try:
                    import PyPDF2
                    with open(cale, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        return '\n'.join(
                            p.extract_text() or '' for p in reader.pages
                        )
                except ImportError:
                    raise ImportError(
                        "Instalează pdfplumber sau PyPDF2:\n"
                        "  pip install pdfplumber"
                    )
        else:
            raise ValueError(f"Format nesupورت: {ext}. Acceptat: .txt, .pdf")


# ─────────────────────────────────────────────
#  MODEL TF-IDF
# ─────────────────────────────────────────────
class ModelTFIDF:
    def __init__(self):
        self.vocabular: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.vectori: list[list[float]] = []
        self.fragmente_meta: list[tuple] = []  # (id, text, sursa)
        self.antrenat = False

    def _tf(self, tokens: list[str]) -> dict[str, float]:
        count = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {t: c / total for t, c in count.items()}

    def _calculeaza_idf(self, documente_tokens: list[list[str]]):
        N = len(documente_tokens)
        df = defaultdict(int)
        for tokens in documente_tokens:
            for t in set(tokens):
                df[t] += 1
        self.idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    def _vectorizeaza(self, tokens: list[str]) -> list[float]:
        tf = self._tf(tokens)
        vec = []
        for cuvant in self.vocabular:
            tfidf = tf.get(cuvant, 0.0) * self.idf.get(cuvant, 0.0)
            vec.append(tfidf)
        return vec

    def _norma(self, vec: list[float]) -> float:
        return math.sqrt(sum(x * x for x in vec))

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norma_a = self._norma(a)
        norma_b = self._norma(b)
        if norma_a == 0 or norma_b == 0:
            return 0.0
        return dot / (norma_a * norma_b)

    def antreneaza(self, fragmente_meta: list[tuple]):
        """fragmente_meta = lista de (id, text, sursa)"""
        if not fragmente_meta:
            return

        self.fragmente_meta = fragmente_meta
        proc = Procesor()

        # Tokenizeaza toate fragmentele
        toate_tokens = [proc.tokenizeaza(f[1]) for f in fragmente_meta]

        # Construieste vocabularul
        toate_cuvinte = sorted(set(t for tokens in toate_tokens for t in tokens))
        self.vocabular = {cuvant: i for i, cuvant in enumerate(toate_cuvinte)}

        # Calculeaza IDF
        self._calculeaza_idf(toate_tokens)

        # Vectorizeaza fiecare fragment
        self.vectori = [self._vectorizeaza(tokens) for tokens in toate_tokens]
        self.antrenat = True

    def cauta(self, intrebare: str, top_k: int = TOP_K) -> list[dict]:
        if not self.antrenat or not self.vectori:
            return []

        proc = Procesor()
        tokens_q = proc.tokenizeaza(intrebare)
        vec_q = self._vectorizeaza(tokens_q)

        scoruri = [
            (i, self._cosine(vec_q, vec))
            for i, vec in enumerate(self.vectori)
        ]
        scoruri.sort(key=lambda x: x[1], reverse=True)

        rezultate = []
        for i, scor in scoruri[:top_k]:
            if scor > 0.01:  # prag minim
                frag_id, text, sursa = self.fragmente_meta[i]
                rezultate.append({
                    "text": text,
                    "sursa": sursa,
                    "scor": round(scor, 4)
                })
        return rezultate

    def salveaza(self, cale: str = MODEL_PATH):
        with open(cale, 'wb') as f:
            pickle.dump({
                'vocabular': self.vocabular,
                'idf': self.idf,
                'vectori': self.vectori,
                'fragmente_meta': self.fragmente_meta,
                'antrenat': self.antrenat,
            }, f)

    def incarca(self, cale: str = MODEL_PATH) -> bool:
        if not os.path.exists(cale):
            return False
        with open(cale, 'rb') as f:
            data = pickle.load(f)
        self.vocabular = data['vocabular']
        self.idf = data['idf']
        self.vectori = data['vectori']
        self.fragmente_meta = data['fragmente_meta']
        self.antrenat = data['antrenat']
        return True


# ─────────────────────────────────────────────
#  MOTOR DE RASPUNS
# ─────────────────────────────────────────────
class MotorRaspuns:
    """Genereaza un raspuns bazat pe fragmentele relevante gasite."""

    def genereaza(self, intrebare: str, fragmente: list[dict]) -> str:
        if not fragmente:
            return ("Nu am găsit informații relevante pentru întrebarea ta "
                    "în textele învățate. Încearcă să reformulezi întrebarea "
                    "sau adaugă mai multe texte.")

        # Extrage cuvintele cheie din intrebare
        proc = Procesor()
        cuvinte_cheie = set(proc.tokenizeaza(intrebare))

        # Alege cel mai bun fragment si evidentiaza info relevanta
        cel_mai_bun = fragmente[0]
        text = cel_mai_bun["text"]
        sursa = cel_mai_bun["sursa"]
        scor = cel_mai_bun["scor"]

        # Imparte in propozitii si scoreaza fiecare
        propozitii = re.split(r'(?<=[.!?])\s+', text)
        prop_scoruri = []
        for prop in propozitii:
            tokens_prop = set(proc.tokenizeaza(prop))
            overlap = len(tokens_prop & cuvinte_cheie)
            prop_scoruri.append((prop, overlap))

        prop_scoruri.sort(key=lambda x: x[1], reverse=True)

        # Selecteaza cele mai relevante propozitii (max 3)
        selectate = [p for p, s in prop_scoruri[:3] if s > 0 or len(prop_scoruri) == 1]
        if not selectate:
            selectate = [propozitii[0]] if propozitii else [text[:300]]

        raspuns_principal = ' '.join(selectate)

        # Adauga context din alte fragmente daca exista
        context_extra = ""
        if len(fragmente) > 1:
            surse_extra = list({f["sursa"] for f in fragmente[1:] if f["sursa"] != sursa})
            if surse_extra:
                context_extra = f"\n\n[Informații suplimentare găsite și în: {', '.join(surse_extra[:2])}]"

        calitate = "ridicată" if scor > 0.3 else "medie" if scor > 0.1 else "scăzută"

        return (
            f"{raspuns_principal}\n\n"
            f"📄 Sursă: {sursa} (relevanță {calitate}: {scor})"
            f"{context_extra}"
        )


# ─────────────────────────────────────────────
#  INTERFATA PRINCIPALA
# ─────────────────────────────────────────────
class AIcititor:
    def __init__(self):
        self.db = Database()
        self.model = ModelTFIDF()
        self.motor = MotorRaspuns()
        self.proc = Procesor()
        self._incarca_model()

    def _incarca_model(self):
        """Incearca sa incarce modelul salvat, altfel il construieste din DB."""
        if self.model.incarca():
            return
        # Reconstruieste din baza de date
        fragmente = self.db.get_toate_fragmente()
        if fragmente:
            self.model.antreneaza(fragmente)
            self.model.salveaza()

    def _reantreneaza(self):
        fragmente = self.db.get_toate_fragmente()
        if fragmente:
            print("  ⏳ Se reantrenează modelul...", end='', flush=True)
            self.model.antreneaza(fragmente)
            self.model.salveaza()
            print(f" ✅ ({len(fragmente)} fragmente)")

    def adauga_fisier(self, cale: str):
        cale = cale.strip().strip('"\'')
        if not os.path.exists(cale):
            print(f"  ❌ Fișierul nu există: {cale}")
            return

        nume = Path(cale).name

        if self.db.document_exista(nume):
            inlocuieste = input(f"  ⚠️  '{nume}' există deja. Înlocuiești? (d/n): ").strip().lower()
            if inlocuieste != 'd':
                return

        print(f"  📖 Se citește '{nume}'...", end='', flush=True)
        try:
            continut = self.proc.citeste_fisier(cale)
            continut = self.proc.curata(continut)
        except Exception as e:
            print(f"\n  ❌ Eroare: {e}")
            return

        if len(continut.split()) < 10:
            print("\n  ❌ Textul este prea scurt sau gol.")
            return

        print(f" {len(continut.split())} cuvinte")

        # Salveaza in DB
        fragmente = self.proc.fragmenteaza(continut)
        doc_id = self.db.salveaza_document(nume, continut, cale)
        self.db.salveaza_fragmente(doc_id, fragmente)
        print(f"  💾 Salvat: {len(fragmente)} fragmente în baza de date")

        # Reantreneaza
        self._reantreneaza()

    def adauga_text_direct(self, nume: str, text: str):
        text = self.proc.curata(text)
        if len(text.split()) < 10:
            print("  ❌ Textul este prea scurt.")
            return

        fragmente = self.proc.fragmenteaza(text)
        doc_id = self.db.salveaza_document(nume, text)
        self.db.salveaza_fragmente(doc_id, fragmente)
        print(f"  💾 Salvat: {len(fragmente)} fragmente")
        self._reantreneaza()

    def intreaba(self, intrebare: str) -> str:
        if not self.model.antrenat:
            return "⚠️  Niciun text învățat încă. Adaugă fișiere mai întâi."

        fragmente = self.model.cauta(intrebare)
        return self.motor.genereaza(intrebare, fragmente)

    def listeaza_documente(self):
        docs = self.db.get_documente()
        if not docs:
            print("  📭 Niciun document în baza de date.")
            return
        print(f"\n  {'ID':<5} {'Nume':<35} {'Cuvinte':<10} {'Adăugat'}")
        print("  " + "-" * 65)
        for doc_id, nume, nr_cuv, data in docs:
            print(f"  {doc_id:<5} {nume[:33]:<35} {nr_cuv:<10} {data}")
        print(f"\n  Total: {self.db.nr_documente()} documente, "
              f"{self.db.nr_fragmente()} fragmente")

    def sterge_document(self, doc_id: int):
        self.db.sterge_document(doc_id)
        print(f"  🗑️  Document {doc_id} șters.")
        self._reantreneaza()


# ─────────────────────────────────────────────
#  MENIU
# ─────────────────────────────────────────────
SEP = "─" * 60

def afis_meniu():
    print(f"\n{SEP}")
    print("  🧠 AI CITITOR  |  Comenzi disponibile")
    print(SEP)
    print("  1  Adaugă fișier (.txt / .pdf)")
    print("  2  Adaugă text direct")
    print("  3  Pune o întrebare")
    print("  4  Vezi documente învățate")
    print("  5  Șterge un document")
    print("  0  Ieși")
    print(SEP)


def main():
    print(SEP)
    print("  🧠 AI CITITOR DE TEXTE")
    print("  Model: TF-IDF + Cosine Similarity | SQLite")
    print(SEP)

    ai = AIcititor()

    n_doc = ai.db.nr_documente()
    if n_doc > 0:
        print(f"  ✅ {n_doc} document(e) în memorie, gata de întrebări.")
    else:
        print("  📭 Niciun document învățat. Adaugă un fișier pentru început.")

    while True:
        afis_meniu()
        cmd = input("  > ").strip()

        if cmd == '0':
            print("\n  👋 La revedere!\n")
            break

        elif cmd == '1':
            cale = input("  Calea fișierului: ").strip()
            ai.adauga_fisier(cale)

        elif cmd == '2':
            nume = input("  Numele documentului: ").strip() or "text_manual"
            print("  Scrie textul (termini cu o linie goală + Enter):\n")
            linii = []
            while True:
                linie = input()
                if linie == "" and linii and linii[-1] == "":
                    break
                linii.append(linie)
            text = '\n'.join(linii).strip()
            if text:
                ai.adauga_text_direct(nume, text)

        elif cmd == '3':
            if not ai.model.antrenat:
                print("  ⚠️  Adaugă cel puțin un document mai întâi.")
                continue
            print()
            while True:
                intrebare = input("  ❓ Întrebarea (sau 'inapoi'): ").strip()
                if intrebare.lower() in ('inapoi', 'back', 'q', ''):
                    break
                raspuns = ai.intreaba(intrebare)
                print(f"\n  {'─'*55}")
                print("  🤖 RĂSPUNS:")
                for linie in raspuns.split('\n'):
                    print(f"     {linie}")
                print(f"  {'─'*55}\n")

        elif cmd == '4':
            ai.listeaza_documente()

        elif cmd == '5':
            ai.listeaza_documente()
            try:
                doc_id = int(input("\n  ID document de șters: "))
                confirmare = input(f"  Sigur ștergi documentul {doc_id}? (d/n): ")
                if confirmare.lower() == 'd':
                    ai.sterge_document(doc_id)
            except ValueError:
                print("  ❌ ID invalid.")

        else:
            print("  ❌ Comandă necunoscută.")


if __name__ == "__main__":
    main()
