from functools import partial
import geopandas, math, maup

def compute_county_ratios():
    """Compute the senate and house ratios for each county in Ohio.

    Returns: (county_house_ratios, county_sen_ratios) a tuple of dictionaries whose keys are
    county codes and whose values are ratios.
    """

    blocks = geopandas.read_file("oh_pl2020_p1_b.zip")

    # record county codes
    county_codes = set([block["COUNTY"] for i, block in blocks.iterrows()])
    county_pops = {c: 0 for c in county_codes}

    # find population of each county
    for i, block in blocks.iterrows():
        county_pops[block["COUNTY"]] += block["P0010001"]

    # compute ideal senate/house population
    state_pop = sum([pop for pop in county_pops.values()])
    sen_pop = state_pop / 33
    house_pop = state_pop / 99

    # compute senate and house ratios for each county
    county_sen_ratios = {c: pop / sen_pop for c, pop in county_pops.items()}
    county_house_ratios = {c: pop / house_pop for c, pop in county_pops.items()}

    return county_house_ratios, county_sen_ratios




def compute_swap_c_h_assignments():
    c_map = geopandas.read_file("oh_counties.zip")
    h_map = geopandas.read_file("oh_sldl_adopted_2022.zip")

    # projection CRS to compute overlaps correctly
    c_map = c_map.to_crs(epsg=26916)
    h_map = h_map.to_crs(epsg=26916)

    # given county, what house districts overlap with county
    # use integer keys because maup will use row index in its assignments
    c_h_assign = {c: [] for c in range(88)}

    # computes which house districts overlap with which counties
    # area cut off 0 not working
    # area cut off .01 to remove boundaries
    overlaps = maup.intersections(c_map, h_map, area_cutoff=0.01)

    # store the assignments in dictionaries
    for index, values in overlaps.items():
        county, h_dist = index
        c_h_assign[county].append(h_dist)

    return(c_h_assign)

def compute_swap_ohio_county_violations(partition,
                                        c_h_assign,
                                        county_house_ratios,
                                        county_sen_ratios,
                                        c_map):
    # compute county overlaps based on house map

    # given county, what senate districts overlap
    c_s_assign = {c: [] for c in c_h_assign.keys()}

    # given senate, what counties overlap
    s_c_assign = {s: [] for s in range(33)}

    # for each county, iterate over house districts that intersect it
    # find their senate assignment, and add to dictionary
    for county, h_list in c_h_assign.items():
        for h_dist in h_list:
            s = partition.assignment[h_dist]
            if s not in c_s_assign[county]:
                c_s_assign[county].append(s)

    for county, s_list in c_s_assign.items():
        for s_dist in s_list:
            s_c_assign[s_dist].append(county)

    # the types of violations in the assignment
    b_1_1, b_1_2, b_2 = 0, 0, 0

    for county_code, sen_ratio in county_sen_ratios.items():
        # need to convert county code to index in c_map
        county = c_map.index[c_map['COUNTY'] == county_code].tolist()[0]

        # (B)(2)
        # Counties having less than one senate ratio of representation,
        # but at least one house of representatives ratio of representation,
        # shall be part of only one senate district.
        if sen_ratio < .95 and county_house_ratios[county_code] >= .95:
            if len(c_s_assign[county]) > 1:
                b_2 += 1

        elif sen_ratio >= .95:

            # compute number of senate districts wholly within county
            wholly_within = 0
            for s in c_s_assign[county]:
                if len(s_c_assign[s]) == 1:
                    wholly_within += 1

            # (B)(1)(1)
            # A county having at least one whole senate ratio of representation shall have
            # as many senate districts wholly within the boundaries of the county as it has
            # whole senate ratios of representation.

            # if statement handles case that .95 floors to 0 but counts as 1 senate ratio
            if sen_ratio < 1:
                if wholly_within != 1:
                    b_1_1 += 1
            else:
                if wholly_within != math.floor(sen_ratio):
                    b_1_1 += 1

            # (B)(1)(2)
            # Any fraction of the population in excess of a whole ratio
            # shall be a part of only one adjoining senate district.
            if sen_ratio > 1.05:
                if len(c_s_assign[county]) > math.ceil(sen_ratio):
                    b_1_2 += 1
    return ([b_1_1, b_1_2, b_2])


def compute_recom_ohio_county_violations(partition,
                           county_house_ratios,
                           county_sen_ratios,
                           county_split_updater="county_splits"):
    # at the moment the assigned senate dsitricts dont match the actual ones in index, but this
    # is almost certainly b/c maup does not know what the actual numbers are

    # keys are counties, values are senate districts in that county
    c_s_assign = {c: list(partition[county_split_updater][c][2]) for c in county_house_ratios.keys()}

    # keys are senate districts, values are counties in that senate district
    s_c_assign = {s: [] for s in range(33)}

    for county, s_list in c_s_assign.items():
        for s_dist in s_list:
            s_c_assign[s_dist].append(county)

    # the types of violations in the assignment
    b_1_1, b_1_2, b_2 = 0, 0, 0

    for county_code, sen_ratio in county_sen_ratios.items():
        # (B)(2)
        # Counties having less than one senate ratio of representation,
        # but at least one house of representatives ratio of representation,
        # shall be part of only one senate district.
        if sen_ratio < .95 and county_house_ratios[county_code] >= .95:
            if len(c_s_assign[county_code]) > 1:
                b_2 += 1

        elif sen_ratio >= .95:

            # compute number of senate districts wholly within county
            wholly_within = sum([1 for s in c_s_assign[county_code] if len(s_c_assign[s]) == 1])
            # wholly_within = 0
            #             for s in c_s_assign[county_code]:
            #                 if len(s_c_assign[s]) == 1:
            #                     wholly_within += 1

            # (B)(1)(1)
            # A county having at least one whole senate ratio of representation shall have
            # as many senate districts wholly within the boundaries of the county as it has
            # whole senate ratios of representation.

            # if statement handles case that .95 floors to 0 but counts as 1 senate ratio
            if sen_ratio < 1:
                if wholly_within != 1:
                    b_1_1 += 1
            else:
                if wholly_within != math.floor(sen_ratio):
                    b_1_1 += 1

            # (B)(1)(2)
            # Any fraction of the population in excess of a whole ratio
            # shall be a part of only one adjoining senate district.
            if sen_ratio > 1.05:
                if len(c_s_assign[county_code]) > math.ceil(sen_ratio):
                    b_1_2 += 1
    return ([b_1_1, b_1_2, b_2])


def ohio_recom_county_violations(county_house_ratios,
                           county_sen_ratios,
                           county_split_updater="county_splits"):

    return(partial(compute_recom_ohio_county_violations,
                   county_house_ratios=county_house_ratios,
                           county_sen_ratios = county_sen_ratios,
                           county_split_updater=county_split_updater))


def ohio_swap_county_violations(c_h_assign, county_house_ratios, county_sen_ratios, c_map):

    return partial(compute_swap_ohio_county_violations,
                                        c_h_assign = c_h_assign,
                                        county_house_ratios = county_house_ratios,
                                        county_sen_ratios = county_sen_ratios,
                                        c_map = c_map)