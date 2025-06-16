# Prepare Fonts

## Install fontforge

``` bash
sudo apt install fontforge
```

## open font file

``` bash
fontforge <fontname>.ttf
```

## Edit font info

Element > Font Info

PS Names:

```
Fontname: OpenSansCondensedBold
Family Name: OpenSansCondensedBold
Name for Humans: OpenSansCondensedBold
Weight: Medium
```

TTF Names:
```
Family: OpenSansCondensedBold
Fullname: OpenSansCondensedBold
Styles (SubFamily): Normal

Remove Preferred Family and Preferred Styles
```

OS/2:
```
Misc:
Width Class: Medium (100%)
Weight Class: 500 Medium
Panose:
Weight: Medium
```

accept change UUID

## Generate new font

File > Generate Fonts

Select TrueType

Uncheck validate

Save
