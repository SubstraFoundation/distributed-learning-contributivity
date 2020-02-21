"""
Created on Fri Nov  29 18:04:13 2019
A script to  run simulations with the truncated Monte-Carlo method 

@author: Thomas-Galtier
"""
 
import numpy as np 
import scenario
import fl_training

from scipy.stats import norm


def truncated_MC(scenario, sv_accuracy=0.01, alpha=0.9, contrib_accuracy=0.05):
    """Return the vector of approximated shapeley value corresponding to a list of node and a characteristic function using the truncated monte-carlo method."""
    
    preprocessed_node_list = scenario.node_list
    n = len(preprocessed_node_list)
    
    # We store the value of the characteristic function in order to avoid recomputing it twice
    char_value_dict={():0} # the dictionary that will countain the values
    listn=np.arange(n)
    
    # Return the characteristic function of the nodelist associated to the ensemble permut, without recomputing it if it was already computed
    def not_twice_characteristic(permut):
        # Sort permut
        permut=np.sort(permut)
        try: # Return the characteristic_func(permut) if it was already computed
            return char_value_dict[tuple(permut)]
        except KeyError: # Characteristic_func(permut) has not been computed yet, so we compute, store, and return characteristic_func(permut)
            small_node_list = np.array([preprocessed_node_list[i] for i in permut])
            char_value_dict[tuple(permut)] = fl_training.compute_test_score(small_node_list,
                              scenario.epoch_count,
                              scenario.x_esval,
                              scenario.y_esval,
                              scenario.x_test,
                              scenario.y_test,
                              scenario.is_early_stopping,
                              save_folder=scenario.save_folder)
            
            return char_value_dict[tuple(permut)]

        
    characteristic_all_node= not_twice_characteristic(np.arange(n)) # Characteristic function on all nodes
    if n==1:
        return({'sv': characteristic_all_node,'std_sv': np.array([0]),'prop': np.array([1]), 'computed_val':char_value_dict})
    else: 
        contributions=np.array([[]])
        permutation=np.zeros(n) # Store the current permutation
        t=0
        q=norm.ppf((1-alpha)/2, loc=0, scale=1)
        v_max=0
        while t<100 or t<q**2 *v_max  /(sv_accuracy*characteristic_all_node)**2 : # Check if the length of the confidence interval  is below the value of sv_accuracy*characteristic_all_node
            t+=1
            print(t)
            print(q**2 *v_max  /(sv_accuracy*characteristic_all_node)**2)
            print()
            
            if t==1:
                contributions=np.array([np.zeros(n)])
            else:
                contributions=np.vstack((contributions, np.zeros(n)))
            
            permutation = np.random.permutation(n) # Store the current permutation 
            char_nodelists = np.zeros(n+1) # Store the characteristic function on each ensemble built with the first elements of the permutation
            char_nodelists[-1]=characteristic_all_node
            for j in range(n):
                if abs(characteristic_all_node-char_nodelists[j])<contrib_accuracy :
                    char_nodelists[j+1] = char_nodelists[j]
                else:
                    char_nodelists[j+1] = not_twice_characteristic(permutation[:j+1])
                contributions[-1][permutation[j]]  =  char_nodelists[j+1]-char_nodelists[j]
            v_max=np.max(np.var(contributions,axis=0))
        sv=np.mean(contributions,axis=0)

    return({'sv':sv, 'std_sv': np.std(contributions,axis=0) / np.sqrt(t-1),'prop':sv/np.sum(sv), 'computed_val':char_value_dict})

        
                
# # TEST:        
# import data_splitting
# import constants
# import itertools
# import shapley_value.shapley as shap
# constants.NB_EPOCHS=5
# constants.BATCH_SIZE=1000
# my_custom_scenario = scenario.Scenario()
# my_custom_scenario.nodes_count=5
# my_custom_scenario.amounts_per_node = [1/my_custom_scenario.nodes_count for i in range ((my_custom_scenario.nodes_count))]
# my_custom_scenario.samples_split_option = 'Random' # or 'Stratified'
# my_custom_scenario.testset_option = 'Centralised' # Toggle between 'Centralised' and 'Distributed'
# my_custom_scenario.x_train = my_custom_scenario.x_train[:5000] # Truncate dataset if needed for quicker debugging/testing
# my_custom_scenario.y_train = my_custom_scenario.y_train[:5000] # Truncate dataset if needed for quicker debugging/testing
# my_custom_scenario.x_test = my_custom_scenario.x_test[:1000] # Truncate dataset if needed for quicker debugging/testing
# my_custom_scenario.y_test = my_custom_scenario.y_test[:1000] # Truncate dataset if needed for quicker debugging/testing

# node_list = data_splitting.process_data_splitting_scenario(my_custom_scenario)
# preprocessed_node_list = fl_training.preprocess_node_list(node_list)
# sv_accuracy,alpha=0.005,0.95
# res1=truncated_MC(preprocessed_node_list, sv_accuracy=sv_accuracy, alpha=alpha, contrib_accuracy=0.001)

# char_value_list=[   res1['computed_val'][tuple(i)]  for r in range(1,my_custom_scenario.nodes_count+1) for i in itertools.combinations(range(my_custom_scenario.nodes_count),r)]
# res1_true=shap.main(my_custom_scenario.nodes_count,char_value_list)
# print(abs(res1['sv']-res1_true) <sv_accuracy)#vrai (1-alpha)% du temps



        

        