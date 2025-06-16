# Asciidoc

You can preview these in various ways, like plugins for IDE's or Google chrome
with the Asciidoctor extension.

For generating a PDF file you'll need:
- asciidoctor
- asciidoctor-diagram
- graphviz
- asciidoctor-pfd

on debian stretch:

```bash
sudo apt-get install graphviz
sudo gem install asciidoctor
sudo gem install asciidoctor-diagram
sudo gem install asciidoctor-pdf --pre
sudo gem install pygments.rb
```

You can generate a pdf from within the `specifications` folder like so:
 `asciidoctor-pdf -r asciidoctor-diagram *.adoc`
