import base64
import time
from random import choice
import matplotlib
import matplotlib.pyplot as plt
import os
from django.conf import settings


class AlignmentScorer:
    traceback_directions = ['Up', 'Left', 'Diagonal', '-']

    # This is used as a lookup for the scoring matrix
    scoring_matrix_indexes = {
        'A': 0,
        'C': 1,
        'G': 2,
        'T': 3,
    }

    def __init__(self, scoring_matrix, indel_penalty):
        self.scoring_matrix = scoring_matrix
        self.indel_penalty = indel_penalty
        self.maximum_match_value = max(list(map(max, scoring_matrix)))

    """Returns a score from the scoring matrix used to initialize AlignmentScorer

    This uses scoring_matrix_indexes as a lookup of what matrix value to use.
    """

    def score(self, nuc_one, nuc_two):
        return self.scoring_matrix[AlignmentScorer.scoring_matrix_indexes[nuc_two]][
            AlignmentScorer.scoring_matrix_indexes[nuc_one]]

    def create_initalized_matrices(self, sequence_one_len, sequence_two_len, global_alignment=True):

        # Create the matrices with 0 and - for default values
        matrix = [[0 for x in range(sequence_one_len + 1)] for y in range(sequence_two_len + 1)]
        traceback_matrix = [['-' for x in range(sequence_one_len + 1)] for y in range(sequence_two_len + 1)]

        # If global alignment is used, fill in the first row and column of the matrices.
        if global_alignment:
            for x in range(sequence_one_len + 1):
                matrix[0][x] = x * self.indel_penalty
            for y in range(sequence_two_len + 1):
                matrix[y][0] = y * self.indel_penalty

            for x in range(sequence_one_len + 1):
                traceback_matrix[0][x] = 'Left'
            for y in range(sequence_two_len + 1):
                traceback_matrix[y][0] = 'Up'
        return matrix, traceback_matrix

    def compute_score(self, matrix, seq_one, seq_two, x, y, global_alignment=True):

        # Compute the scores from the cells diagonal, above, and to the left of the cell at x, y
        match = self.score(seq_one[x], seq_two[y])
        diag_score = matrix[y][x] + match
        top_score = matrix[y + 1][x] + self.indel_penalty
        left_score = matrix[y][x + 1] + self.indel_penalty

        # Put all the scores into a list
        scores = [left_score, top_score, diag_score]
        if not global_alignment:
            scores.append(0)  # For local alignment, each cell must have a min score of 0.

        # Get the max value of the list
        max_value = max(scores)

        # Get the index of the max argument in the list. Because we initialized the list as [left_score, top_score, diag_score],
        # If the index is 0, we know the direction is left, if the index is 1, we know the direction should be up, and if the index is 2 the direction should be diagonal
        direction = AlignmentScorer.traceback_directions[max(range(len(scores)), key=scores.__getitem__)]

        if not global_alignment and max_value == 0:
            direction = AlignmentScorer.traceback_directions[
                3]  # For the local alignment, we don't want a traceback direction if the corresponding matrix value is 0

        return (max_value, direction)

    def fill_matrices(self, matrix, traceback_matrix, seq_one, seq_two, global_alignment=True):
        # seq_one is on the top of the matrix and seq_two as the left side.
        # We'll loop through the matrices and fill out the values.
        for y in range(len(seq_two)):
            for x in range(len(seq_one)):
                max_value, direction = self.compute_score(matrix, seq_one, seq_two, x, y, global_alignment)
                matrix[y + 1][x + 1] = max_value
                traceback_matrix[y + 1][x + 1] = direction

    """Adds ---- to sequences to fill in the gap

    Example, add_dashes('ATG', [1]) gives A-TG
    Example, add_dashes('ATG', [1,2]) gives A-T-G
    Example, add_dashes('ATG', [], 2) gives --ATG
    Example, add_dashes('ATG', [1,2], 2) gives --A-T-G
    """

    def add_dashes(self, sequence, gaps, offset=0):
        final_sequence = '-' * offset
        for index, char in zip(range(len(sequence)), sequence):
            final_sequence += '-' * gaps.count(index)
            final_sequence += char

        final_sequence += '-' * gaps.count(len(sequence))

        return final_sequence

    # This creates the | between the two sequences in the final output.
    def create_match_string(seq_one, seq_two):
        result = ''
        for a, b in zip(seq_one, seq_two):
            # If the two nucleotides are the same add a |
            if a == b:
                result += '|'
            else:  # Otherwise add a space
                result += ' '
        return result

    def local_alignment_traceback(self, matrix, traceback_matrix, seq_one, seq_two):

        # Start by finding the maximum value in the matrix, along with its x and y coordinates
        max_value = 0
        max_x = 0
        max_y = 0
        for x in range(len(seq_one) + 1):
            for y in range(len(seq_two) + 1):
                if matrix[y][x] > max_value:
                    max_x = x
                    max_y = y
                    max_value = matrix[y][x]

        seq_a_gaps = []
        seq_b_gaps = []

        x = max_x
        y = max_y

        # We will go back through the matrix using the traceback matrix as a guide until we hit 0 in the matrix.
        # When the traceback matrix says to go Up or Left, we will note there should be a gap in the appropriate sequence
        while matrix[y][x] != 0:
            direction = traceback_matrix[y][x]
            if direction == 'Up':
                seq_a_gaps.append(x)  # This means there was a gap in the first sequence
                y -= 1
            if direction == 'Left':
                seq_b_gaps.append(y)  # This means there was a gap in the second sequence
                x -= 1
            if direction == "Diagonal":  # This means there was no gap
                y -= 1
                x -= 1

        gap = x - y

        seq_two_padding = max(gap, 0)  # If gap is positive, add - padding to second sequence
        seq_one_padding = -min(gap, 0)  # If gap is negative, add - padding to first sequence

        # We will align the two sequences using - for gaps. This will line up the sequences so the first shared nucleotide in the local alignment is lined up.
        final_seq_one = self.add_dashes(seq_one, seq_a_gaps, seq_one_padding)
        final_seq_two = self.add_dashes(seq_two, seq_b_gaps, seq_two_padding)

        # We will find the starting and ending points of the aligned region. The | characters will only be added for the area which is locally aligned.
        start_pos = max(x, y)
        end_pos = start_pos + abs(max_x - x)

        # Get the subsections of the sequences which are locally aligned
        matched_sequence_one = final_seq_one[start_pos:end_pos]
        matched_sequence_two = final_seq_two[start_pos:end_pos]

        # We'll now generate the | characters for matching nucleotides in the locally aligned region
        match_line = ' ' * max(x, y) + AlignmentScorer.create_match_string(matched_sequence_one, matched_sequence_two)

        # The maximum possible value is the length of the shorter sequence * the maximum match score
        max_possible_score = self.maximum_match_value * min(len(seq_one), len(seq_two))
        percent_similarity = (100 * max_value) / max_possible_score

        return final_seq_one, match_line, final_seq_two, str(max_value), str(percent_similarity)[:7]
        # return final_seq_one + '\n' + match_line + '\n' + final_seq_two + '\nScore: ' + str(max_value)

    def global_alignment_traceback(self, matrix, traceback_matrix, seq_one, seq_two):
        seq_a_gaps = []
        seq_b_gaps = []

        # Set x and y to be in the bottom right corner of the matrix
        x = len(seq_one)
        y = len(seq_two)

        while x > 0 or y > 0:
            direction = traceback_matrix[y][x]
            if direction == 'Up':
                seq_a_gaps.append(x)  # If the traceback direction is Up, we know there is a gap in the first sequence
                y -= 1
            if direction == 'Left':
                seq_b_gaps.append(
                    y)  # If the traceback direction is Left, we know there is a gap in the second sequence
                x -= 1
            if direction == "Diagonal":  # If the traceback direction is Diagonal, we know there is no gap
                y -= 1
                x -= 1

        # Fill in the gaps with -'s
        final_seq_one = self.add_dashes(seq_one, seq_a_gaps)
        final_seq_two = self.add_dashes(seq_two, seq_b_gaps)

        # The score comes from the bottom right value in the score matrix
        score = matrix[len(seq_two)][len(seq_one)]

        # Return the sequences + the | text where there are matches
        result = final_seq_one + '\n'
        result += AlignmentScorer.create_match_string(final_seq_one, final_seq_two) + '\n'
        result += final_seq_two + '\nScore: ' + str(score)

        # The maximum possible value is the length of the shorter sequence * the maximum match score - the gap in length * the indel score
        longer_sequence_length = max(len(seq_one), len(seq_two))
        shorter_sequence_length = min(len(seq_one), len(seq_two))
        gap = longer_sequence_length - shorter_sequence_length

        max_possible_score = self.maximum_match_value * shorter_sequence_length + (gap * self.indel_penalty)
        percent_similarity = (100 * score) / max_possible_score

        # SPLITTED:
        result1 = final_seq_one
        result2 = AlignmentScorer.create_match_string(final_seq_one, final_seq_two)
        result3 = final_seq_two
        result4_score = str(
            matrix[len(seq_two)][len(seq_one)])
        result5_p_similarity = str(percent_similarity)[:7]
        return result1, result2, result3, result4_score, result5_p_similarity


def get_sequences(path):
    """Returns a list(string) of genetic sequences

    The relative file path of the file containing the genetic sequences
    """
    sequences = []
    current_sequence = ''
    with open(path) as file:
        for line in file:
            if line.startswith('>'):
                if (current_sequence != ''):
                    sequences.append(current_sequence.replace('\n', ''))
                    current_sequence = ''
            else:
                current_sequence += line
        if (current_sequence != ''):
            sequences.append(current_sequence.replace('\n', ''))
    return sequences


# Trim each line to only be x characters long
def truncate_lines(text, characters_show):
    return '\n'.join([line[:characters_show] for line in text.splitlines()])


def main_local(f1_path, f2_path, algo):
    # ALGO
    result1 = ""
    result2 = ""
    result3 = ""
    result4_score = ""
    characters_shown = 20

    indel_penalty = -1
    mismatch = 2
    match = 4
    # Scoring matrix to allow different match scores / mismatch penalties for different nucleotide combinations. For example, an A-C mismatch could be penalized less than an A-G mismatch.
    #                  A        C       G       T
    scoring_matrix = [[match, mismatch, mismatch, mismatch],  # A
                      [mismatch, match, mismatch, mismatch],  # C
                      [mismatch, mismatch, match, mismatch],  # G
                      [mismatch, mismatch, mismatch, match]]  # T

    show_graphs = True

    # Get the file paths for the sequences
    seq_one_path = f1_path
    seq_two_path = f2_path

    # If global_alignment is True, the Needleman–Wunsch algorithm will be used.
    # If global_alignment is False, the Smith–Waterman algorithm will be used.
    global_alignment = algo

    # Read the files
    seq_ones = get_sequences(seq_one_path)
    seq_twos = get_sequences(seq_two_path)

    # Used for ploting the computation time
    times = [0]
    lengths = [0]

    sequence_ones_count = len(seq_ones)
    sequence_twos_count = len(seq_twos)

    # Send a message if either file has more sequences than the other.
    if (sequence_ones_count != sequence_twos_count):
        print(
            f'File {seq_one_path} has {sequence_ones_count} sequences while file {seq_two_path} has {sequence_twos_count} sequences.')

    for seq_one, seq_two in zip(seq_ones, seq_twos):

        start = time.time()

        # We create a scorer. This object holds the scoring_matrix and indel_penalty and is used to run the algorthims
        scorer = AlignmentScorer(scoring_matrix, indel_penalty)

        matrix, traceback_matrix = scorer.create_initalized_matrices(len(seq_one), len(seq_two), global_alignment)

        # This will fill out the empty values in matrix and traceback_matrix
        scorer.fill_matrices(matrix, traceback_matrix, seq_one, seq_two, global_alignment)

        # This will use the filled out matrix and traceback_matrix to find the gaps and generate the output text. The output text will be stored in result.
        result = ''
        if global_alignment == "Global":
            result1, result2, result3, result4_score, result5_p_similarity = scorer.global_alignment_traceback(matrix,
                                                                                                               traceback_matrix,
                                                                                                               seq_one,
                                                                                                               seq_two)
        elif global_alignment == "":
            result1, result2, result3, result4_score, result5_p_similarity = scorer.local_alignment_traceback(matrix,
                                                                                                              traceback_matrix,
                                                                                                              seq_one,
                                                                                                              seq_two)

        end = time.time()

        # Add the runtime of alignment algorthim (seconds) and the length of the longer sequence.
        times.append(end - start)
        lengths.append(max(len(seq_one), len(seq_two)))

        # truncate_lines trims each line of the output to only be characters_shown charters long.
        print(truncate_lines(result, characters_shown))

        # Optional: Print the runtime of the algorthim to the console
        # print('Runtime: ' + str(end - start))

        # Prints 3 blank lines to the console
        print('\n')

    if show_graphs:
        matplotlib.use('Agg')
        lens_sorted, times_sorted = zip(*sorted(zip(lengths, times)))

        plt.plot(lens_sorted, times_sorted)
        plt.ylabel('Time (seconds)')
        plt.xlabel('Sequence length')
        # plt.show()
        plt.savefig(os.path.join(settings.MEDIA_ROOT, 'graph_local.png'), bbox_inches='tight')

        f_path = os.path.join(settings.MEDIA_ROOT, 'graph_local.png')
        with open(f_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        plt.close()

    final_result1 = truncate_lines(result1, characters_shown)
    final_result2 = truncate_lines(result2, characters_shown)
    final_result3 = truncate_lines(result3, characters_shown)
    final_result4_score = truncate_lines(result4_score, characters_shown)

    return final_result1, final_result2, final_result3, final_result4_score, result5_p_similarity, image_data
