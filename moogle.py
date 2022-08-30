###################################################################
# FILE: moogle.py
# WRITER: Daniel Sinai
# DESCRIPTION: This program implements the search engine "Moogle"
###################################################################
import requests
import bs4
import urllib.parse
import sys
import pickle


def create_relatives_list(path):
    """
    This function gets the relative urls from a file
    :param path: Path for the file with the relative urls
    :return: Dictionary with all the relative urls, numbered by indexes
    """
    with open(path) as _:
        relatives_list = _.read().splitlines()
    return relatives_list


def create_full_url(base_url, relative_url):
    """
    This function creates an absolute url from base and relative url
    :param base_url: Base url
    :param relative_url: Relative url
    :return: Combined absolute url
    """
    return urllib.parse.urljoin(base_url, relative_url)


def crawl(base_url, relative_path):
    """
    This function creates a dictionary with the number of links between
    webpages
    :param base_url: Base url of a webpage
    :param relative_path: Path to the index file that contains the
           relative urls
    :return: Dictionary with number of links between the webpages from the
             index file
    """
    relatives_list = create_relatives_list(relative_path)
    traffic_dict = dict()
    for relative in relatives_list:
        inner_dict = dict()
        response = requests.get(create_full_url(base_url, relative))
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        for p in soup.find_all("p"):
            for link in p.find_all("a"):
                target = link.get("href")
                if target in relatives_list:
                    inner_dict[target] = inner_dict.get(target, 0) + 1
        traffic_dict[relative] = inner_dict
    return traffic_dict


def sum_dict(diction):
    """
    This function summarizes a dictionary values
    :param diction: Dictionary to be summarized
    :return: Sum of the dictionary values
    """
    sum1 = 0
    for key in diction:
        sum1 += diction[key]
    return sum1


def create_new_zero_dict(traffic_dict):
    """
    This function creates a dictionary with values of 0 and keys from another
    dictionary
    :param traffic_dict: The dictionary from which we take the keys
    :return: New dictionary with values of 0 and keys from traffic_dict
    """
    zero_dict = dict()
    for key in traffic_dict:
        zero_dict[key] = 0
    return zero_dict


def page_rank(iterations_num, traffic_dict):
    """
    This function ranks a webpages based on their links to and from other
    webpages
    :param iterations_num: Number of iterations for the ranking
    :param traffic_dict: Dictionary that contains the links between all of
           the webpages
    :return: Dictionary with the rank of the pages
    """
    r = dict()
    for key in traffic_dict:
        r[key] = 1

    for i in range(iterations_num):
        new_r = create_new_zero_dict(traffic_dict)
        for key in traffic_dict:
            for inner_key in traffic_dict[key]:
                all_link_sum = sum_dict(traffic_dict[key])
                new_r[inner_key] += r[key] * ((traffic_dict[key][inner_key])
                                              / all_link_sum)
        r = new_r
    return r


def words_dict(base_url, index_path):
    """
    This function calculates how many times each word in the webpages is shown
    in all of the webpages
    :param base_url: Base url to work with
    :param index_path: Path to the relative urls file
    :return: Dictionary with the number of performance of each word in the
             Webpages
    """
    word_dict = dict()
    relatives_list = create_relatives_list(index_path)
    for relative in relatives_list:
        response = requests.get(create_full_url(base_url, relative))
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        for p in soup.find_all("p"):
            content = p.text
            words_list = content.split()
            for word in words_list:
                if word not in word_dict:
                    word_dict[word] = dict()
                if relative in word_dict[word]:
                    word_dict[word][relative] += 1
                else:
                    word_dict[word][relative] = 1
    return word_dict


def sort_dict(dictionary):
    """
    This function sorts a dictionary
    :param dictionary: Dictionary to be sorted
    :return: Sorted dictionary
    """
    sorted_dictionary = {}
    sorted_keys = sorted(dictionary, key=dictionary.get, reverse=True)
    for key in sorted_keys:
        sorted_dictionary[key] = dictionary[key]
    return sorted_dictionary


def sort_list_by_values(sorted_dict):
    """
    This function sorts a list according to a dictionary values
    :param sorted_dict: Sorted dictionary
    :return: Sorted list according to the dictionary values
    """
    sorted_list = []
    for key in sorted_dict:
        sorted_list.append(key)
    return sorted_list


def filter_max_dict(query_list, sorted_rank_dict, word_dict, max_results):
    """
    This function filters the ranking dictionary to max_results pages
    :param query_list: List of query word/s
    :param sorted_rank_dict: Sorted ranking dictionary
    :param word_dict: Words dictionary
    :param max_results: Num of pages to be on the final dictionary
    :return: Filtered dictionary with max_results pages
    """
    sorted_relatives_list = sort_list_by_values(sorted_rank_dict)
    max_results_dict = dict()
    for relative in sorted_relatives_list:
        if relative in sorted_rank_dict:
            flag = True
            for q in query_list:
                if q not in word_dict:
                    continue
                else:
                    if relative not in word_dict[q]:
                        flag = False
                        break
            if flag and len(max_results_dict) < max_results:
                max_results_dict[relative] = sorted_rank_dict[relative]
    return max_results_dict


def search(query, ranking_dict, word_dict, max_results):
    """
    This function runs a query search on the webpages and return the results
    in a dictionary
    :param query: A query
    :param ranking_dict: The ranking dictionary
    :param word_dict: The words dictionary
    :param max_results: Num of webpages to be displayed
    :return: Dictionary with the search results
    """
    query_list = query.split()
    sorted_rank_dict = sort_dict(ranking_dict)
    max_results_dict = filter_max_dict(query_list, sorted_rank_dict, word_dict,
                                       max_results)

    final_ranking_dict = dict()
    for key in max_results_dict:
        num_of_appearances = []
        if len(query_list) == 1:
            if query in word_dict:
                final_ranking_dict[key] = max_results_dict[key] * \
                                          word_dict[query][key]
        else:
            for q in query_list:
                if q not in word_dict:
                    continue
                else:
                    num_of_appearances.append(word_dict[q][key])
            if len(num_of_appearances) > 0:
                word_rank = min(num_of_appearances)
                final_ranking_dict[key] = max_results_dict[key] * word_rank
    final_ranking_dict = sort_dict(final_ranking_dict)
    return final_ranking_dict


def run_search(query, ranking_dict, word_dict, max_results):
    """
    This function runs a single search in Moogle engine
    :param query: A query
    :param ranking_dict: The ranking dictionary
    :param word_dict: The words dictionary
    :param max_results:
    :return:
    """
    final_ranking_dict = search(query, ranking_dict, word_dict, max_results)
    for key, value in final_ranking_dict.items():
        print(key, value)


if __name__ == "__main__":
    command_type = sys.argv[1]
    if command_type == "crawl":
        base_link, index_file, out_file = sys.argv[2], sys.argv[3], sys.argv[4]
        final_traffic_dict = crawl(base_link, index_file)
        with open(out_file, "wb") as f:
            pickle.dump(final_traffic_dict, f)

    elif command_type == "page_rank":
        iterations, dict_file, out_file = int(sys.argv[2]),\
                                          sys.argv[3], sys.argv[4]
        with open(dict_file, "rb") as f:
            d = pickle.load(f)
        final_pagerank_dict = page_rank(iterations, d)
        with open(out_file, "wb") as f:
            pickle.dump(final_pagerank_dict, f)

    elif command_type == "words_dict":
        base_link, index_file, out_file = sys.argv[2], sys.argv[3], sys.argv[4]
        final_word_dict = words_dict(base_link, index_file)
        with open(out_file, "wb") as f:
            pickle.dump(final_word_dict, f)

    elif command_type == "search":
        user_query, ranking_dict_path, words_dict_path, user_max_results = \
            sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
        with open(ranking_dict_path, "rb") as f:
            ranking_dict_file = pickle.load(f)
        with open(words_dict_path, "rb") as f:
            words_dict_file = pickle.load(f)
        run_search(user_query, ranking_dict_file, words_dict_file,
                   user_max_results)
    else:
        print("Illegal command!")
        sys.exit()
