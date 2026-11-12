DISPOSAL = {
 "plastic": "Rinse and dry, then place in the dry-recyclables bin. Check the resin code (1-7); remove caps and labels where possible. Avoid burning plastic.",
 "paper": "Keep dry and clean, flatten boxes, and place in the paper recycling bin. Greasy or wet paper (e.g. pizza boxes) should go to compost or general waste.",
 "metal": "Rinse cans and tins, then place in the metal recycling bin. Take scrap metal and e-waste to an authorised scrap or recycling centre.",
 "glass": "Rinse and place in the glass bin, separated by colour if required. Wrap broken glass safely; do not mix ceramics or mirrors with bottle glass.",
 "organic": "Compost at home or use the wet-waste/green bin. Keep it free of plastic, and consider home composting or biogas collection.",
}
def recommendation(cat): return DISPOSAL[cat]
