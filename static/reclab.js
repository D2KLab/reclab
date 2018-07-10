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
        for (let dataset in configs['datasets']) {
            if (dataset === json['dataset']) {
                let name = configs['datasets'][dataset]['name'];
                let option = $('<option>');
                option.attr('value', dataset);
                option.text(name);
                datasets.append(option);
                $('#dataset-help').text(configs['datasets'][dataset]['desc']);
            }
        }

        // Splitters
        let splitters = $('#splitter').prop('disabled', true);
        for (let splitter in configs['splitters']) {
            if (splitter === json['splitter']) {
                let name = configs['splitters'][splitter]['name'];
                let option = $('<option>');
                option.attr('value', splitter);
                option.text(name);
                splitters.append(option);
                $('#splitter-help').text(configs['splitters'][splitter]['desc']);
            }
        }

        // Recommenders
        let recommenders = $('#recommenders').prop('disabled', true);
        for (let recommender in configs['recommenders']) {
            let name = configs['recommenders'][recommender]['name'];
            let option = $('<option>');
            option.attr('value', recommender);
            option.text(name);
            if (!$.inArray(recommender, json['recommenders'])) {
                option.attr('selected', 'selected');
            }
            recommenders.append(option);
        }

        // Values
        $("#ratio").val(json['test_size'] * 100).prop('disabled', true);
        $("#length").val(json['k']).prop('disabled', true);
        $("#threshold").val(json['threshold']).prop('disabled', true);
    }

    function initializeForm() {
        // Datasets
        let datasets = $('#dataset');
        for (let dataset in configs['datasets']) {
            let name = configs['datasets'][dataset]['name'];
            let option = $('<option>');
            option.attr('value', dataset);
            option.text(name);
            datasets.append(option);
        }

        datasets.change(function () {
            let value = $("#dataset option:selected").first().attr("value");
            $('#dataset-help').text(configs['datasets'][value]['desc']);
        });

        datasets.change();

        // Splitters
        let splitters = $('#splitter');
        for (let splitter in configs['splitters']) {
            let name = configs['splitters'][splitter]['name'];
            let option = $('<option>');
            option.attr('value', splitter);
            option.text(name);
            splitters.append(option);
        }

        splitters.change(function () {
            let value = $("#splitter option:selected").first().attr("value");
            $('#splitter-help').text(configs['splitters'][value]['desc']);
        });

        splitters.change();

        // Recommenders
        let recommenders = $('#recommenders');
        for (let recommender in configs['recommenders']) {
            let name = configs['recommenders'][recommender]['name'];
            let option = $('<option>');
            option.attr('value', recommender);
            option.attr('selected', 'selected');
            option.text(name);
            recommenders.append(option);
        }

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
        for (let metric in configs['metrics']) {
            tr.append($('<th>').text(configs['metrics'][metric]['name']));
        }

        for (let i = 0; i < json['results'].length; i++) {
            let tr = $('<tr>');
            table.append(tr);
            let recommender = json['results'][i]['name'];
            tr.append($('<td>').text(configs['recommenders'][recommender]['name']));
            if (json['results'][i]['status'] === 'done') {
                for (let metric in configs['metrics']) {
                    tr.append($('<td>').text(json['results'][i][metric].toFixed(6)));
                }
            } else if (json['results'][i]['status'] === 'running') {
                running = true;
                for (let metric in configs['metrics']) {
                    tr.append($('<td>').text('Running'));
                }
            } else {
                for (let metric in configs['metrics']) {
                    tr.append($('<td>').text('Failed'));
                }
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
            $.getJSON('/experiment/' + exp_id, function (json) {
                let running = createResultsTable(json);
                if (json['results'].length !== json['recommenders'].length || running === true) {
                    setTimeout(updateResults, counter * 1000);
                } else {
                    $('.btn').prop('disabled', false);
                }
            });
        }

        $.ajax({
            url: '/experiment',
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
        $.getJSON('/experiment/' + exp_id, function (json) {
            initializeImmutableForm(json);
            let running = createResultsTable(json);
            if (json['results'].length !== json['recommenders'].length || running === true) {
                setTimeout(loadExperiment, counter * 1000);
            }
        });
    }

    $.getJSON('/config', function (json) {
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