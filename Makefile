.PHONY: all fetchlinksgoogle fetchlinksddg fetchprofilesgoogle fetchprofilesddg

all: fetchlinksgoogle fetchlinksddg fetchprofilesgoogle fetchprofilesddg

fetchlinksgoogle:
	python gather_links/sele_google.py dataset/T1_dataset.json output/google_links.json

fetchlinksddg:
	python gather_links/sele_ddg.py dataset/T1_dataset.json output/ddg_links.json

fetchprofilesgoogle:
	python gather_linkedin_info/lala.py output/google_links.json linkedin/linkedin_profiles_all_google.json

fetchprofilesddg:
	python gather_linkedin_info/lala.py output/ddg_links.json linkedin/linkedin_profiles_all_ddg.json

fetchprofilesddg_my:
	python gather_linkedin_info/sele_linkedin_oop.py output/ddg_links.json linkedin/linkedin_profiles_all_ddg_oop.json

google:
	fetchlinksgoogle
	fetchprofilesgoogle

ddg:
	fetchlinksddg
	fetchprofilesddg

everything:
	google
	ddg

	python get_input.py
	python gather_links/sele_google.py temp/input.json temp/google_links.json
	python gather_links/sele_ddg.py temp/input.json temp/ddg_links.json
	python transform.py
	python gather_linkedin_info/sele_linkedin_BD.py temp/merged_links.json temp/all_linkedin_profiles.json	
run:
	python gather_linkedin_info/sele_linkedin_BD.py temp/merged_links.json temp/all_linkedin_profiles.json	
	python get_similarity.py
	python get_final_rankings.py
	python confidence_scores.py
	

