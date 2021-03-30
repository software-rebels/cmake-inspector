from algorithms import removeDuplicatesFromFlattedList
import pickle
file = open('flatten_merged_result_2.pickle', 'rb')
flatted = pickle.load(file)
removeDuplicatesFromFlattedList(flatted)
