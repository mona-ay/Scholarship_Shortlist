import gradio as gr
import matplotlib.pyplot as plt
import time


def parse_applicants(text):
    # This function takes raw text input and converts it into structured applicant data.
    # It also validates input and returns errors if something is wrong.

    applicants = []

    if text.strip() == "":
        return None, "Please enter at least one applicant."

    lines = text.strip().split("\n")

    for i in range(len(lines)):
        if lines[i].strip() == "":
            continue

        parts = lines[i].split(",")

        if len(parts) != 4:
            return None, "Line " + str(i + 1) + " must be: Name, GPA, Volunteer Hours, Essay Score"

        name = parts[0].strip()

        try:
            gpa = float(parts[1].strip())
            volunteer_hours = float(parts[2].strip())
            essay_score = float(parts[3].strip())
        except:
            return None, "Line " + str(i + 1) + " has a non-number value."

        if name == "":
            return None, "Line " + str(i + 1) + " is missing a name."

        # Validate ranges
        if gpa < 0 or gpa > 4.3:
            return None, "Line " + str(i + 1) + ": GPA must be between 0 and 4.3."

        if volunteer_hours < 0:
            return None, "Line " + str(i + 1) + ": Volunteer hours cannot be negative."

        if essay_score < 0 or essay_score > 100:
            return None, "Line " + str(i + 1) + ": Essay score must be between 0 and 100."

        # Convert GPA to percentage for consistent scoring
        gpa_percent = (gpa / 4.3) * 100

        # Cap volunteer hours so extreme values do not dominate ranking
        volunteer_score = min(volunteer_hours, 100)

        # Score formula (design choice):
        # Final Score = 50% GPA + 20% Volunteer Hours + 30% Essay Score
        final_score = (0.50 * gpa_percent) + (0.20 * volunteer_score) + (0.30 * essay_score)

        applicants.append({
            "name": name,
            "gpa": gpa,
            "volunteer_hours": volunteer_hours,
            "essay_score": essay_score,
            "final_score": final_score
        })

    if len(applicants) == 0:
        return None, "Please enter at least one valid applicant."

    return applicants, None


def format_score(score):
    return str(round(score, 2))


def make_chart(applicants, title, highlight_name, status, bars_to_show):
    # This function creates the bar chart visualization for the current step.

    shown = applicants[:bars_to_show]

    names = []
    scores = []
    colors = []

    for p in shown:
        names.append(p["name"])
        scores.append(p["final_score"])

        # Color logic to highlight sorting process
        if status == "complete":
            colors.append("lime")
        elif p["name"] == highlight_name:
            colors.append("yellow")
        else:
            colors.append("hotpink")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(names, scores, color=colors)

    ax.set_ylim(0, 100)
    ax.set_title(title)
    ax.set_ylabel("Final Score")

    # Display score values above bars
    for i in range(len(scores)):
        ax.text(i, scores[i] + 1, format_score(scores[i]), ha="center")

    plt.xticks(rotation=20)
    plt.tight_layout()
    return fig


def format_ranking(applicants):
    # Converts final sorted list into readable text output.

    text = ""
    for i in range(len(applicants)):
        p = applicants[i]
        text += (
            str(i + 1) + ". " + p["name"] +
            " | Score: " + format_score(p["final_score"]) +
            " | GPA: " + str(p["gpa"]) +
            " | Hours: " + str(p["volunteer_hours"]) +
            " | Essay: " + str(p["essay_score"]) + "\n"
        )
    return text


def merge(left, right, steps):
    # This function merges two already sorted lists into one sorted list.
    # It also records each step so the visualization can show progress.

    merged = []
    i = 0
    j = 0

    steps.append({"list": left + right, "highlight": "", "msg": "Merging two sorted groups"})

    while i < len(left) and j < len(right):
        # Compare the highest remaining scores from both halves.
        # The larger score is placed first (descending order).
        if left[i]["final_score"] >= right[j]["final_score"]:
            chosen = left[i]
            i += 1
        else:
            chosen = right[j]
            j += 1

        merged.append(chosen)

        # Record step for visualization
        steps.append({
            "list": merged + left[i:] + right[j:],
            "highlight": chosen["name"],
            "msg": "Placing: " + chosen["name"]
        })

    # Add any remaining elements from the left half
    while i < len(left):
        merged.append(left[i])
        steps.append({"list": merged, "highlight": left[i]["name"], "msg": "Adding remaining (left)"})
        i += 1

    # Add any remaining elements from the right half
    while j < len(right):
        merged.append(right[j])
        steps.append({"list": merged, "highlight": right[j]["name"], "msg": "Adding remaining (right)"})
        j += 1

    return merged


def merge_sort(arr, steps):
    # Base case: a list with 0 or 1 element is already sorted.
    if len(arr) <= 1:
        return arr

    # Split the list into two halves
    mid = len(arr) // 2

    # Recursively sort both halves
    left = merge_sort(arr[:mid], steps)
    right = merge_sort(arr[mid:], steps)

    # Merge the sorted halves back together
    return merge(left, right, steps)


def run_animation(text, top_n, bars, speed):
    # This function runs the full simulation and yields each step for Gradio animation.

    data, err = parse_applicants(text)
    if err:
        yield err, "", "", None
        return

    try:
        top_n = int(top_n)
        bars = int(bars)
        speed = float(speed)
    except:
        yield "Invalid inputs.", "", "", None
        return

    steps = []
    steps.append({"list": data, "highlight": "", "msg": "Start: Original list"})

    # Perform merge sort while collecting visualization steps
    sorted_list = merge_sort(data, steps)

    for i in range(len(steps)):
        step = steps[i]

        chart = make_chart(
            step["list"],
            "Step " + str(i + 1),
            step["highlight"],
            "sorting",
            bars
        )

        yield "", "", step["msg"], chart
        time.sleep(speed)

    final_chart = make_chart(sorted_list, "Final Ranking", "", "complete", bars)

    yield format_ranking(sorted_list), format_ranking(sorted_list[:top_n]), "Done!", final_chart


with gr.Blocks(title="Scholarship Shortlist Simulator") as demo:
    gr.Markdown("# Scholarship Shortlist Simulator")

    with gr.Row():
        with gr.Column():
            input_box = gr.Textbox(
                lines=10,
                value="Mona,4.1,80,92\nAli,3.7,120,88\nSara,4.3,60,95\nOmar,3.9,90,84\nLina,4.0,100,98"
            )

            top_n = gr.Number(value=3, label="Top N")

            bars = gr.Slider(1, 10, value=5, step=1, label="Bars to show")

            speed = gr.Slider(0.2, 2.0, value=1.0, step=0.1, label="Speed")

            btn = gr.Button("Run")

        with gr.Column():
            full = gr.Textbox(label="Full Ranking")
            short = gr.Textbox(label="Shortlist")

    msg = gr.Textbox(label="Step Explanation")
    plot = gr.Plot()

    btn.click(
        run_animation,
        inputs=[input_box, top_n, bars, speed],
        outputs=[full, short, msg, plot]
    )


demo.launch()