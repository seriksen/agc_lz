def get_files(server_location: str, search_path: str, outfile: str|None=None, search_range: list | None=None) -> list:

    if server_location == "nersc":
        prefix = "/global/cfs/cdirs/"
        all_files = get_files_nersc(prefix + search_path, search_range)
    elif server_location == "dirac":
        prefix = "root://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/lz"
        raise ValueError("server location")
    else:
        raise ValueError(f"{server_location} is not a valid location")

    if outfile is not None:
        with open(outfile, 'w') as f:
            for line in all_files:
                f.write(line)
                f.write('\n')

    return all_files

def get_files_nersc(search_path: str, search_range: list | None=None) -> list:

    import glob
    file_dirs = glob.glob(search_path)

    if search_range:
        file_dirs = [f for f in file_dirs if float(f[f.rfind('_')+1:]) >= search_range[0] and float(f[f.rfind('_')+1:]) <= search_range[1]]

    all_files = []
    for f in file_dirs:
        all_files.extend(glob.glob(f + '/rq/*.root'))

    return all_files


