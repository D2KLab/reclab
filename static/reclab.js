$(function () {
    let configs;
    let exp_id;
    let counter = 1;

    function initializeImmutableForm(json) {
        if ($('.btn').prop('disabled') === true)
            return;
        $('.btn').prop('disabled', true);

        // Datasets
        let datasets = $('#dataset').prop('disabled', true);
        configs['datasets'].forEach(function (dataset) {
             if (dataset['id'] === json['dataset']) {
                let name = dataset['name'];
                let option = $('<option>');
                option.attr('value', dataset['id']);
                option.text(name);
                datasets.append(option);
                $('#dataset-help').text(dataset['desc']);
            }
        });

        // Splitters
        let splitters = $('#splitter').prop('disabled', true);
        configs['splitters'].forEach(function (splitter) {
            if (splitter['id'] === json['splitter']) {
                let name = splitter['name'];
                let option = $('<option>');
                option.attr('value', splitter['id']);
                option.text(name);
                splitters.append(option);
                $('#splitter-help').text(splitter['desc']);
            }
        });

        // Recommenders
        let recommenders = $('#recommenders').prop('disabled', true);
        configs['recommenders'].forEach(function (recommender) {
            let name = recommender['name'];
            let option = $('<option>');
            option.attr('value', recommender['id']);
            option.text(name);
            if (json['recommenders'].includes(recommender['id'])) {
                option.attr('selected', 'selected');
            }
            recommenders.append(option);
        });

        // Values
        $("#ratio").val(json['test_size'] * 100).prop('disabled', true);
        $("#length").val(json['k']).prop('disabled', true);
        $("#threshold").val(json['threshold']).prop('disabled', true);
    }

    function initializeForm() {
        // Datasets
        let datasets = $('#dataset');
        configs['datasets'].forEach(function (dataset) {
            let name = dataset['name'];
            let option = $('<option>');
            option.attr('value', dataset['id']);
            option.text(name);
            datasets.append(option);
        });

        datasets.change(function () {
            let value = $("#dataset option:selected").first().attr("value");
            configs['datasets'].forEach(function (dataset) {
                if (dataset['id'] === value) {
                    $('#dataset-help').text(dataset['desc']);
                }
            });
        });

        datasets.change();

        // Splitters
        let splitters = $('#splitter');
        configs['splitters'].forEach(function (splitter) {
            let name = splitter['name'];
            let option = $('<option>');
            option.attr('value', splitter['id']);
            option.text(name);
            splitters.append(option);
        });

        splitters.change(function () {
            let value = $("#splitter option:selected").first().attr("value");
            configs['splitters'].forEach(function (splitter) {
                if (splitter['id'] === value) {
                    $('#splitter-help').text(splitter['desc']);
                }
            });
        });

        splitters.change();

        // Recommenders
        let recommenders = $('#recommenders');
        configs['recommenders'].forEach(function (recommender) {
            let name = recommender['name'];
            let option = $('<option>');
            option.attr('value', recommender['id']);
            option.text(name);
            recommenders.append(option);
        });

        // Values
        $("#ratio").val(20);
        $("#length").val(10);
        $("#threshold").val(3);
    }

    function createResultsTable(json) {
        counter++;
        let running = false;
        let result = $('#result').empty();

        let h3 = $('<h3>').text('Experiment #' + json['id']);
        result.append(h3);
        let table = $('<table>').addClass('table');
        result.append(table);
        let tr = $('<tr>');
        table.append(tr);
        tr.append($('<th>').text('Algorithm'));
        configs['metrics'].forEach(function (metric) {
            tr.append($('<th>').text(metric['name']));
        });

        for (let i = 0; i < json['results'].length; i++) {
            let tr = $('<tr>');
            table.append(tr);
            let recommender_id = json['results'][i]['name'];
            configs['recommenders'].forEach(function (recommender) {
                if (recommender['id'] === recommender_id) {
                    tr.append($('<td>').text(recommender['name']));
                }
            });
            if (json['results'][i]['status'] === 'done') {
                configs['metrics'].forEach(function (metric) {
                    if (json['results'][i][metric['id']] !== undefined) {
                        tr.append($('<td>').text(json['results'][i][metric['id']].toFixed(6)));
                    } else {
                        tr.append($('<td>'));
                    }
                });
            } else if (json['results'][i]['status'] === 'running') {
                running = true;
                configs['metrics'].forEach(function () {
                    tr.append($('<td>').text('Running'));
                });
            } else {
                configs['metrics'].forEach(function () {
                    tr.append($('<td>').text('Failed'));
                });
            }
        }

        let url = window.location.protocol + '//' + window.location.host +
            window.location.pathname + '?id=' + json['id'];
        let p = $('<p>').html('This experiment is available at <a href="' + url + '">' + url + '</a>. RecLab version ' + json['version'] + '.');
        result.append(p);

        return running
    }

    $('#run-experiment').submit(function () {
        $('.btn').prop('disabled', true);
        $('#result').empty();
        counter = 1;

        let form = $(this);
        let exp = {
            dataset: form.find("#dataset").val(),
            splitter: form.find("#splitter").val(),
            test_size: form.find("#ratio").val() / 100,
            k: form.find("#length").val(),
            threshold: form.find("#threshold").val(),
            recommenders: form.find("#recommenders").val()
        };

        function updateResults() {
            $.getJSON('experiment/' + exp_id, function (json) {
                let running = createResultsTable(json);
                if (json['results'].length !== json['recommenders'].length || running === true) {
                    setTimeout(updateResults, counter * 1000);
                } else {
                    $('.btn').prop('disabled', false);
                }
            });
        }

        $.ajax({
            url: 'experiment',
            type: "post",
            data: JSON.stringify(exp),
            dataType: "json",
            contentType: "application/json",
            success(json) {
                exp_id = json['id'];
                updateResults();
            }
        });

        return false;
    });

    function getId() {
        let searchString = window.location.search.substring(1);
        let searchSplit = searchString.split('&');
        for (let i = 0; i < searchSplit.length; i++) {
            let searchName = searchSplit[i].split('=');
            if (searchName[0] === 'id') {
                return searchName[1];
            }
        }
    }

    function loadExperiment() {
        $.getJSON('experiment/' + exp_id, function (json) {
            initializeImmutableForm(json);
            let running = createResultsTable(json);
            if (json['results'].length !== json['recommenders'].length || running === true) {
                setTimeout(loadExperiment, counter * 1000);
            }
        });
    }

    $.getJSON('config', function (json) {
        configs = json;
        let id = getId();
        if (id > 0) {
            exp_id = id;
            loadExperiment();
        } else {
            initializeForm();
        }
    });

});