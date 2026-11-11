"""Generate a regular 2D multi-bay, multi-storey frame model from reviewed inputs."""

def build_regular_frame(bays, storeys, bay_width_m, storey_height_m,
                        beam_width_mm, beam_depth_mm, column_width_mm,
                        column_depth_mm, elastic_modulus_gpa):
    if not (1 <= int(bays) <= 8 and 1 <= int(storeys) <= 8):
        raise ValueError("Bays and storeys must be between 1 and 8.")
    if min(bay_width_m, storey_height_m, beam_width_mm, beam_depth_mm,
           column_width_mm, column_depth_mm, elastic_modulus_gpa) <= 0:
        raise ValueError("Geometry, section dimensions and elastic modulus must be positive.")
    E = elastic_modulus_gpa * 1_000_000.0  # GPa -> kN/m²
    bw, bd = beam_width_mm/1000, beam_depth_mm/1000
    cw, cd = column_width_mm/1000, column_depth_mm/1000
    Ab, Ib = bw*bd, bw*bd**3/12
    Ac, Ic = cw*cd, cw*cd**3/12
    nodes=[]
    for level in range(int(storeys)+1):
        for ix in range(int(bays)+1):
            nodes.append({"id":f"N{level}_{ix}","x_m":ix*bay_width_m,"y_m":level*storey_height_m})
    members=[]
    for level in range(int(storeys)+1):
        for ix in range(int(bays)):
            members.append({"id":f"B{level+1}_{ix+1}","i":f"N{level}_{ix}","j":f"N{level}_{ix+1}","E_kN_m2":E,"A_m2":Ab,"I_m4":Ib,"type":"Beam","section_mm":f"{int(beam_width_mm)} × {int(beam_depth_mm)}"})
    for level in range(int(storeys)):
        for ix in range(int(bays)+1):
            members.append({"id":f"C{level+1}_{ix+1}","i":f"N{level}_{ix}","j":f"N{level+1}_{ix}","E_kN_m2":E,"A_m2":Ac,"I_m4":Ic,"type":"Column","section_mm":f"{int(column_width_mm)} × {int(column_depth_mm)}"})
    supports={f"N0_{ix}":[True,True,True] for ix in range(int(bays)+1)}
    return {"nodes":nodes,"members":members,"supports":supports,"bays":int(bays),"storeys":int(storeys),"bay_width_m":float(bay_width_m),"storey_height_m":float(storey_height_m),"material":{"elastic_modulus_gpa":float(elastic_modulus_gpa)},"sections":{"beam":{"width_mm":beam_width_mm,"depth_mm":beam_depth_mm},"column":{"width_mm":column_width_mm,"depth_mm":column_depth_mm}}}
