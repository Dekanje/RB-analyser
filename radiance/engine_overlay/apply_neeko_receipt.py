"""Add private diagnostic registration receipts; not agent observation."""
from pathlib import Path
from apply_elnuk_errata import once

def apply(root):
    p=root/"src/main.cpp"
    old='            for (auto id : d.sideboard)    line("side    ", id);'
    new=old+'\n            std::cout << "    neeko_count " << d.neeko_legends.size() << "\\n";\n            for (auto id : d.neeko_legends) line("neeko   ", id);'
    p.write_text(once(p.read_text(),old,new))
if __name__=="__main__":
    apply(Path("alpharune"))
