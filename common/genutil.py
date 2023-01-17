from calyx import py_ast as ast


def build_mem(comp, name, width, size, is_external=True, is_ref=False):
    """Build a Calyx memory cell.

    Adds a `seq_mem_d1` cell to `comp` with the given element `width`
    and element count `size`. Optionally set the @external and @ref
    attributes.
    """
    # The exception for 1-element memories is something of a wart
    # in Calyx: they should have zero-bit address ports, but Calyx
    # doesn't like that.
    idx_width = (size - 1).bit_length() if size > 1 else 1

    # Parameterize the memory component.
    comp.prog.import_("primitives/memories.futil")
    inst = ast.CompInst("seq_mem_d1", [width, size, idx_width])

    # Create a cell.
    return comp.cell(name, inst, is_external=is_external, is_ref=is_ref)
