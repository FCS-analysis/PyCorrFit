This folder contains the TeX-source of the 
[PyCorrFit documentation](https://github.com/FCS-analysis/PyCorrFit/wiki/PyCorrFit_doc.pdf).

If, for some reason, you wish to compile it yourself, you will need a 
working LaTeX distribution.

If you are running a Linux system, make sure that the following packages
are installed:

    ghostscript  
    texlive  
    texlive-base  
    texlive-bibtex-extra  
    texlive-latex-extra  
    texlive-math-extra  
    texlive-science  
    
    
Apply these commands repeatedly (3 times to be on the safe side) to
build the documentation:
    
    pdflatex -synctex=1 -interaction=nonstopmode PyCorrFit_doc.tex     
    bibtex PyCorrFit_doc.aux  
