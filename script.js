$(document).ready(function () {
    var table = $('#example').DataTable({
        processing: true,
        serverSide: true,
        ajax: function (data, callback) {
            // Log the order data to debug
            console.log(data.order); // This will show the sorting array

            var page = Math.floor(data.start / data.length) + 1;
            var limit = data.length;
            var searchValue = data.search.value;

            console.log(page, limit)

            // Define a mapping of column indices to column names
            var columnNames = [
                'product_name', // index 0
                'category_id',  // index 1
                'price',        // index 2
                'stock',        // index 3
                'created_at',   // index 4
                'updated_at'    // index 5
            ];
            
            let sort_column = "";
            let sort_direction= "";

            if (data.order != null) {
                sort_column = columnNames[data.order[0].column - 1];
                sort_direction = data.order[0].dir;
                console.log(sort_column, sort_direction)
            }

            $.ajax({
                url: `http://127.0.0.1:5000/api/v1/products/read`,
                type: 'GET',
                data: {
                    limit: limit,
                    page: page,
                    search: searchValue,
                    sort_column: sort_column,
                    sort_direction: sort_direction
                },
                success: function (response) {
                    callback({
                        draw: data.draw,
                        data: response.datas,
                        recordsTotal: response.pagination.total_items,
                        recordsFiltered: response.pagination.total_items
                    });
                }
            });
        },
        columns: [
            { data: null, title: 'No.', render: function(data, type, row, meta) { return meta.row + 1 + meta.settings._iDisplayStart; } },
            { data: 'product_name', title: 'Product Name' },
            { data: 'category_name', title: 'Category Name' },
            { data: 'price', title: 'Price', render: $.fn.dataTable.render.number(',', '.', 2, '$') },
            { data: 'stock', title: 'Stock' },
            { data: 'created_at', title: 'Created At' },
            { data: 'updated_at', title: 'Updated At' }
        ],
        dom: "lfrtip",
        select: true,
        pageLength: 5,
        lengthMenu: [
            [3, 5, 10, 25, 50, -1], // Options for the number of rows
            [3, 5, 10, 25, 50, "All"] // Labels for the options
        ]
    });
});
