"""
LaTeX compiler for combining contents of various sections and compiling to PDF.
"""

import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class LatexCompiler:
    """
    LaTeX compiler for combining LaTeX content from various sections and compiling to PDF.
    
    This class is responsible for:
    1. Generating a complete LaTeX document structure
    2. Combining content from various sections
    3. Compiling the LaTeX document to PDF
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the LaTeX compiler.
        
        Args:
            output_dir (str, optional): Path to the output directory. If None, the current directory is used.
        """
        self.output_dir = output_dir or '.'
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def compile_report(
        self,
        title: str,
        author: str,
        section_files: Dict[str, str],
        image_files: List[str] = None,
        output_filename: str = "simulation_report",
        abstract: str = None
    ) -> str:
        """
        Compile a complete research report.
        
        Args:
            title (str): Report title.
            author (str): Report author.
            section_files (Dict[str, str]): Dictionary of section content file paths in {section_name: file_path} format.
            image_files (List[str], optional): List of paths to image files.
            output_filename (str, optional): Output filename (without extension).
            abstract (str, optional): Report abstract.
            
        Returns:
            str: Path to the generated PDF file.
        """
        # Generate complete LaTeX content
        latex_content = self.generate_latex_document(
            title=title, 
            author=author, 
            section_files=section_files, 
            abstract=abstract
        )
        
        # Compile to PDF from content
        return self.compile_report_from_content(
            title=title,
            author=author,
            latex_content=latex_content,
            image_files=image_files,
            output_filename=output_filename,
            abstract=abstract
        )
    
    def compile_report_from_content(
        self,
        title: str,
        author: str,
        latex_content: str,
        image_files: List[str] = None,
        output_filename: str = "simulation_report",
        abstract: str = None
    ) -> str:
        """
        Compile a report to PDF from LaTeX content.
        
        Args:
            title (str): Report title.
            author (str): Report author.
            latex_content (str): Complete LaTeX document content.
            image_files (List[str], optional): List of paths to image files.
            output_filename (str, optional): Output filename (without extension).
            abstract (str, optional): Report abstract.
            
        Returns:
            str: Path to the generated PDF file.
        """
        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy image files to temporary directory
            image_paths = []
            if image_files:
                for img_path in image_files:
                    img_filename = os.path.basename(img_path)
                    dest_path = os.path.join(temp_dir, img_filename)
                    shutil.copy2(img_path, dest_path)
                    image_paths.append(img_filename)
            
            # Write LaTeX content to temporary file
            tex_file_path = os.path.join(temp_dir, f"{output_filename}.tex")
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF
            self._compile_latex(temp_dir, output_filename)
            
            # Copy generated PDF to output directory
            pdf_path = os.path.join(temp_dir, f"{output_filename}.pdf")
            output_path = os.path.join(self.output_dir, f"{output_filename}.pdf")
            
            if os.path.exists(pdf_path):
                shutil.copy2(pdf_path, output_path)
                return output_path
            else:
                raise RuntimeError("PDF generation failed")
    
    def generate_latex_document(
        self,
        title: str,
        author: str,
        section_files: Dict[str, str],
        abstract: Optional[str] = None
    ) -> str:
        """
        Generate a complete LaTeX document.
        
        Args:
            title (str): Report title.
            author (str): Report author.
            section_files (Dict[str, str]): Dictionary of section content file paths.
            abstract (str, optional): Report abstract.
            
        Returns:
            str: Generated LaTeX document content.
        """
        preamble = self._generate_preamble(title, author)
        
        document_begin = "\\begin{document}\n\n\\maketitle\n\n"
        
        # Add abstract (if provided)
        abstract_section = ""
        if abstract:
            abstract_section = "\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n\n"
        
        # Add table of contents
        toc = "\\tableofcontents\n\\newpage\n\n"
        
        # Add content from each section
        sections_content = ""
        section_order = [
            "Research Objectives",
            "Simulation Setup",
            "Experimental Results",
            "Conclusion"
        ]
        
        for section_name in section_order:
            if section_name in section_files:
                # Read section content
                with open(section_files[section_name], 'r', encoding='utf-8') as f:
                    section_content = f.read()
                
                # Add section command and content
                sections_content += f"\\section{{{section_name}}}\n\n{section_content}\n\n"
        
        document_end = "\\end{document}"
        
        # Combine complete document
        full_document = preamble + document_begin + abstract_section + toc + sections_content + document_end
        
        return full_document
    
    def _generate_preamble(self, title: str, author: str) -> str:
        """
        Generate the LaTeX document preamble.
        
        Args:
            title (str): Report title.
            author (str): Report author.
            
        Returns:
            str: LaTeX document preamble content.
        """
        return f"""\\documentclass[12pt,a4paper]{{article}}

% Basic packages
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{microtype}}
\\usepackage{{amsmath,amssymb,amsfonts}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{hyperref}}

% Page setup
\\usepackage[top=2.5cm,bottom=2.5cm,left=2.5cm,right=2.5cm]{{geometry}}

% Figure and table setup
\\usepackage{{float}}
\\usepackage{{caption}}
\\usepackage{{subcaption}}

% Bibliography
\\usepackage{{natbib}}
\\bibliographystyle{{plainnat}}

% Title and author
\\title{{{title}}}
\\author{{{author}}}
\\date{{\\today}}

% Hyperlink setup
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
    pdftitle={{{title}}},
    pdfauthor={{{author}}},
    pdfsubject={{Multi-Agent Social Simulation}},
    pdfkeywords={{simulation, multi-agent, social}}
}}

"""
    
    def _compile_latex(self, working_dir: str, filename: str) -> None:
        """
        Compile LaTeX document to PDF.
        
        Args:
            working_dir (str): Path to the working directory.
            filename (str): Filename (without extension).
        """
        # Change to working directory
        original_dir = os.getcwd()
        os.chdir(working_dir)
        
        try:
            # Run pdflatex twice to resolve cross-references
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", f"{filename}.tex"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
        except subprocess.CalledProcessError as e:
            print(f"LaTeX compilation error: {e}")
            # Continue execution so log files can be checked
        except FileNotFoundError:
            print("pdflatex command not found. Please ensure you have a LaTeX distribution like TeX Live or MiKTeX installed.")
        finally:
            # Change back to original directory
            os.chdir(original_dir) 