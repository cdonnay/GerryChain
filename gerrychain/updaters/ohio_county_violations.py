from functools import partial
import geopandas, math

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
