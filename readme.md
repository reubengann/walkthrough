# Walkthrough compiler

This program parses a simple text file format for a video game walkthrough and produces an html page with interactive collectible checklists.

See the data folder for some examples.

## Input file syntax

Any given line in the input file can either be a special directive or a normal line. If it's a normal line, it is parsed as a paragraph.

## Special directives

### Version number

For example
```
\version{1}
```

This is used internally by the Javascript in the page. If a new version is released, all of the old tags should be invalidated, as you may have inserted or removed checklist items and the old storage cannot understand the new structure.

### Declarations

In the preamble of the file you should declare the kinds of collectible that are in your document

```
\declare{lunchbox}{Lunch Box}{Lunch Boxes}
```

Here we define the tag name "lunchbox", the proper name "Lunch Box" and the plural "Lunch Boxes". These are used in producing section headings.

### Title

```
\title{Alan Wake 2}
```

Defines the title of the walkthrough.

### Section

```
\section{Introduction}
\section{Return 1: Invitation: Cauldron Lake}{Return 1}
```

Defines a new section of the walkthrough. This name is used to label collectibles in the "all checklist items" and "all items by section" parts of the walkthrough. In the second example, we define an abbreviated name for those lists. Otherwise the full name will be used.

### Unnumbered lists

```
\begin{ul}
\item Bullet point 1
\item Bullet point 2
\end{ul}
```

Defines a bullet point list. Each line needs an \item tag. Once \begin{ul} has been called, \end{ul} must be found.

### Checklist

```
\checklist
```

Tells the compiler to place a summary checklist of all checklist items in this part here. The next time you call \checklist it will only print the new checklist items since the last checklist.

### Spoiler

```
\begin{spoiler}

Put a puzzle solution or other info someone might not want to see here.

\end{spoiler}
```

Defines a paragraph that should be initially collapsed/not visible, with a message that the reader can click to reveal the puzzle solution.

Within a spoiler, you can can include an image:

```
\begin{spoiler}

A II has two stacked triangles facing up. III has two side-by-side triangles facing down. Stand on the triangle and look down to see I which is two triangles stacked facing down.

\img{stash_2_solution.png}

\end{spoiler}
```

The file in this example `stash_2_solution.png` must exist in the same folder as the source text file.

## Regular lines

If a line doesn't begin with one of the above special directives, it is assumed to be a normal paragraph. The things allowed in a paragraph are:

### Regular text

This will be output as regular text

### Checklist item

```
Walk forward and take the [key|Special Key].

In a break room you'll find [manpage|Manuscript Page: Scratch on the Hunt|Scratch on the Hunt]
```

A checklist item for a collectible is surrounded by square brackets. Arguments of the checklist item are delimited by pipes (the | symbol). 
- The first argument must be a collectible code that was previously declared in the declarations. 
- The second argument is the name as it will appear in the paragraph text. 
- The third argument is optional, and is the way it will show up in the summary checklists. If unspecified, the full text will show up in the checklist.

### Link

```
If you find a problem with this guide, please report it at \link{https://github.com/reubengann/walkthrough} in the issues section.
```

This will insert a hyperlink to that address.

## Setup

It's recommended to set up a virtual environment. If using conda:

```bash
conda create -n walkthrough python=3.11
conda activate walkthrough
pip install -r requirements.in
pip install -r requirements-dev.in
```

Otherwise, use whatever environment management you like.

## Command line arguments

### Compile

```bash
python walkthrough.py compile c:\walkthroughs\game1.txt
```

Compiles the html into the same folder as the source. Used while you're writing the walkthrough.

### Watch

```bash
python walkthrough.py watch c:\walkthroughs\game1.txt
```

Same as `compile`, but it will monitor the input file and recompile when changes are detected. Useful when you are writing the walkthrough and don't want to have to issue the `compile` command over and over.

### Build

```bash
python walkthrough.py build c:\walkthroughs\game1.txt
```

This compiles the html and zips it up along with all of the images. Good for distributing your walkthrough.
