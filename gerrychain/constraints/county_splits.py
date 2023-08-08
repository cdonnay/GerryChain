def valid_county_splits_swap(partition):
    return(sum(partition["swap_ohio_county_violations"]) == 0)

def valid_county_splits_recom(partition):
    return(sum(partition["recom_ohio_county_violations"]) == 0)