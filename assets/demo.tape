# Regenerate with: vhs assets/demo.tape  (needs vhs, ttyd, winsyms and pdblister on PATH)
# then shrink it; the raw render is ~10 MB because the progress bar changes every frame:
#   ffmpeg -i assets/demo.gif -vf "fps=10,mpdecimate,split[a][b];[a]palettegen=max_colors=32:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" -fps_mode vfr small.gif
#   mv small.gif assets/demo.gif
Output assets/demo.gif

Require winsyms
Require pdblister

# Not bash: on Windows that resolves to WSL, which can't see the Windows winsyms install
Set Shell pwsh
Set FontSize 16
Set Width 1150
Set Height 420
Set Padding 20
Set Framerate 15
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

# Short fixed dir outside the repo: winsyms prints the absolute output path, and a
# %TEMP% path would leak the local username into the GIF
Hide
Type "Remove-Item -Recurse -Force C:\winsyms-demo -ErrorAction Ignore; Set-Location (New-Item -ItemType Directory C:\winsyms-demo); function prompt { '> ' }; Clear-Host"
Enter
Show

Type "winsyms list 26100.1297"
Sleep 400ms
Enter
Sleep 2.5s

Type "winsyms get 26100.1297 --path-prefix windows/system32/drivers/"
Sleep 400ms
Enter
Wait+Screen@60s /Success!/
Sleep 2.5s

Type "dir symbols -Name | select -First 8"
Sleep 400ms
Enter
Sleep 4s
