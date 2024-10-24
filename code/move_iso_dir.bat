for /D %%s in (.\*) do (
    echo "Directory %%s"
    if exist "%%s\setup.exe" (
        echo "Renaming"
        ren %%s unpacked_dir
        exit 0
    )
)
echo "Directory not found"
exit 1