from hmm import HMM
import pandas as pd
import numpy as np
import random
import pprint
import time
import csv
import os
import re

pp = pprint.PrettyPrinter(indent=4)


def prediction_hmm_candidate_test():
    print("### HMM Candidates - Evaluation")

    hmm = HMM(1, max_edits=2, max_states=3)

    print("\n Starting training…")
    start = time.time()

    hmm.train(words_ds="../data/word_freq/frequency-alpha-gcide.txt",
              sentences_ds="../data/texts/big_clean.txt",
              typo_ds="../data/typo/new/train.csv")

    end = time.time()
    train_time = end - start

    print("Endend training in {:4.2f} seconds".format(train_time))
    print("\n Starting testing…")
    start = time.time()

    real = []
    observed = []

    with open("../data/typo/new/test.csv", "r") as f:
        reader = csv.reader(f)
        obs = [row for row in reader]

        iterator = 0
        for el in obs:
            if iterator % 100 == 0:
                print(iterator)
            iterator += 1

            real.append(el[1])
            if len(hmm.candidates(el[0])) > 0:
                observed.append(hmm.candidates(el[0])[0][0])
            else:
                observed.append("") # if no word is bredicted by the model
                print(el, "No words predicted", "\n")

    end = time.time()
    test_time = end - start
    print("Endend testing in {:6.2f} seconds \n".format(test_time))

    # save prediction to csv
    d = {'real': real, 'observed': observed}
    prediction = pd.DataFrame(d)

    if not os.path.exists("../results"):
        os.makedirs("../results")

    prediction.to_csv("../results/typo_evaluation.csv", sep=',', index=False)


def evaluation_hmm_candidate_test():
    predictions = pd.read_csv("../results/typo_evaluation.csv")

    print("\n Starting evaluation…")
    start = time.time()
    predictions['count'] = np.where(predictions['real'] == predictions['observed'], True, False)

    frequencies = predictions['count'].value_counts(True)
    accuracy = frequencies[True]

    end = time.time()
    eval_time = end - start

    print("Ended evaluation in {:6.2f} seconds \n".format(eval_time))

    print("Accuracy: {:4.2f} %".format(accuracy*100))

    # Add accuracy top-3 and top-5


def perturb(hmm):
    cleaned = open("../data/texts/big_clean.txt", "r")

    if not os.path.exists("../data/texts/perturbated/"):
        os.makedirs("../data/texts/perturbated/")

    perturbed = open("../data/texts/perturbated/big_perturbed.txt", "w")

    for line in cleaned:
        pos = 0
        while pos < len(line):
            if line[pos].isalpha():
                char_select = line[pos]
                c = random.random()
                if c <= 0.1:
                    # Given a char selected randomly from the line,
                    # replace it with a new char chosen randomly from the given neighbours in the hmm error model
                    cran = random.choice(list(hmm.error_model["sub"][char_select.lower()].keys()))
                    initial = line[0:pos]
                    final = line[pos + 1:]
                    line = initial + cran + final
                pos += 1
            else:
                pos += 1
            if pos == len(line):
                perturbed.write(line)


def prediction_hmm_sequence_test():
    print("### HMM Sequence Prediction - Evaluation")

    # Cleaning dataset
    with open("../data/texts/big_clean.txt", "r") as f:
        real = f.readlines()
        real = [r.replace("\n", "") for r in real]

    print("\n Start training…")

    start = time.time()

    hmm = HMM(1, max_edits=2, max_states=3)
    hmm.train(words_ds="../data/word_freq/frequency-alpha-gcide.txt",
              sentences_ds="../data/texts/big_clean.txt",
              typo_ds="../data/typo/new/train.csv")

    end = time.time()
    train_time = end - start

    print("Endend training in {:4.2f} seconds".format(train_time))

    print("\n Starting perturbation…")
    start = time.time()

    perturb(hmm)

    end = time.time()
    perturbation_time = end - start
    print("Endend perturbation in {:4.2f} seconds".format(perturbation_time))

    print("\n Start testing…")
    start = time.time()

    observed = []

    with open("../data/texts/perturbated/big_perturbed.txt", "r") as f:
        perturbated = f.readlines()
        perturbated = [p.replace("\n", "") for p in perturbated]

        iterator = 0
        for sentence in perturbated:
            if sentence == '':
                continue
            if iterator % 100 == 0:
                print(iterator)
            iterator += 1
            corrected = hmm.predict_sequence(sentence)
            observed.append(corrected)

    end = time.time()
    test_time = end - start
    print("Endend testing in {:6.2f} seconds \n".format(test_time))

    # save prediction to csv
    d = {'target': real, 'perturbated': perturbated, 'observed': observed}
    prediction = pd.DataFrame(d)

    if not os.path.exists("../results"):
        os.makedirs("../results")

    prediction.to_csv("../results/sentence_prediction.csv", sep=',', index=False)


def evaluation_hmm_sequence_test():
    predictions = pd.read_csv("../results/sentence_prediction.csv")

    print("\n Starting evaluation…")
    start = time.time()
    predictions['exact_match'] = np.where(predictions['target'] == predictions['observed'], True, False)

    exact_match_frequencies = predictions['exact_match'].value_counts(True)

    if True not in exact_match_frequencies.keys():
        exact_match_accuracy = 0
    else:
        exact_match_accuracy = exact_match_frequencies[True]

    for index, row in predictions.iterrows():
        target = row["target"].split()
        prediction = row["observed"].split()
        noisy = row["perturbated"].split()

        total = len(target)

        perturbated = 0
        not_perturbated = 0

        correct_prediction = 0
        not_correct_prediction = 0

        correct_perturbated = 0
        not_corrected_perturbated = 0

        corrected_not_perturbated = 0
        not_corrected_not_perturbated = 0

        for i, word in enumerate(target):
            is_perturbated = (target[i] != noisy[i])
            is_correct = (target[i] == prediction[i])

            if is_perturbated:
                perturbated += 1
            else:
                not_perturbated += 1

            if is_correct:
                correct_prediction += 1
            else:
                not_correct_prediction += 1

            if is_perturbated and is_correct:
                correct_perturbated += 1
            elif is_perturbated and not is_correct:
                not_corrected_perturbated += 1
            elif not is_perturbated and is_correct:
                corrected_not_perturbated += 1
            else:
                not_corrected_not_perturbated += 1

        predictions.loc[index, 'correct'] = perturbated / total
        predictions.loc[index, 'not_correct'] = not_perturbated / total
        predictions.loc[index, 'correct PREV correct'] = corrected_not_perturbated / not_perturbated
        predictions.loc[index, 'correct PREV not_correct'] = not_corrected_not_perturbated / not_perturbated
        predictions.loc[index, 'not_correct PREV correct'] = correct_perturbated / perturbated
        predictions.loc[index, 'not_correct PREV not_correct'] = not_corrected_perturbated / perturbated
        predictions.loc[index, 'accuracy'] = correct_prediction / total
        predictions.loc[index, 'precision'] = corrected_not_perturbated / (corrected_not_perturbated + correct_perturbated)
        predictions.loc[index, 'recall'] = corrected_not_perturbated / (corrected_not_perturbated + not_corrected_not_perturbated) # same of sensitivity
        predictions.loc[index, 'specificity'] = not_corrected_perturbated / (not_corrected_perturbated + corrected_not_perturbated)

    word_accuracy = np.mean(predictions['accuracy'])
    word_precision = np.mean(predictions['precision'])
    word_recall = np.mean(predictions['recall'])
    word_specificity = np.mean(predictions['specificity'])

    end = time.time()
    eval_time = end - start

    print("Ended evaluation in {:6.2f} seconds \n".format(eval_time))

    print("Exact match accuracy: {:4.2f} %".format(exact_match_accuracy * 100))
    print("Word accuracy: {:4.2f} %".format(word_accuracy * 100))
    print("Word precision: {:4.2f} %".format(word_precision * 100))
    print("Word recall: {:4.2f} %".format(word_recall * 100))
    print("Word specificity: {:4.2f} %".format(word_specificity * 100))

    predictions.to_csv("../results/sentence_evaluation.csv", sep=',', index=False)

# prediction_hmm_candidate_test()
# evaluation_hmm_candidate_test()

# prediction_hmm_sequence_test()
evaluation_hmm_sequence_test()

