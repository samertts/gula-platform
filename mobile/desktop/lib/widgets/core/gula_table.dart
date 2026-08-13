import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import 'gula_loading.dart';

class GulaTableColumn {
  final String key;
  final String label;
  final double? flex;
  final double? width;
  final TextAlign? textAlign;
  final bool sortable;
  final Widget Function(dynamic value, Map<String, dynamic> row)? cellBuilder;
  final String? Function(dynamic value)? sortValue;

  GulaTableColumn({
    required this.key,
    required this.label,
    this.flex,
    this.width,
    this.textAlign,
    this.sortable = false,
    this.cellBuilder,
    this.sortValue,
  });
}

class GulaTable extends StatefulWidget {
  final List<GulaTableColumn> columns;
  final List<Map<String, dynamic>> rows;
  final String? keyField;
  final bool isLoading;
  final bool isSelectable;
  final bool isSortable;
  final bool showCheckboxes;
  final Set<String>? selectedKeys;
  final ValueChanged<Set<String>>? onSelectionChanged;
  final VoidCallback? onRefresh;
  final int? page;
  final int? totalPages;
  final int? totalItems;
  final ValueChanged<int>? onPageChanged;
  final int? rowsPerPage;
  final ValueChanged<int>? onRowsPerPageChanged;
  final String? emptyMessage;
  final double? rowHeight;
  final Widget? Function(Map<String, dynamic> row)? contextMenuBuilder;

  const GulaTable({
    super.key,
    required this.columns,
    required this.rows,
    this.keyField = 'id',
    this.isLoading = false,
    this.isSelectable = false,
    this.isSortable = false,
    this.showCheckboxes = false,
    this.selectedKeys,
    this.onSelectionChanged,
    this.onRefresh,
    this.page,
    this.totalPages,
    this.totalItems,
    this.onPageChanged,
    this.rowsPerPage,
    this.onRowsPerPageChanged,
    this.emptyMessage,
    this.rowHeight,
    this.contextMenuBuilder,
  });

  @override
  State<GulaTable> createState() => _GulaTableState();
}

class _GulaTableState extends State<GulaTable> {
  String? _sortColumn;
  bool _sortAscending = true;
  Set<String> _selectedKeys = {};

  @override
  void initState() {
    super.initState();
    if (widget.selectedKeys != null) {
      _selectedKeys = Set.from(widget.selectedKeys!);
    }
  }

  @override
  void didUpdateWidget(GulaTable oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selectedKeys != null) {
      _selectedKeys = Set.from(widget.selectedKeys!);
    }
  }

  List<Map<String, dynamic>> get _sortedRows {
    if (_sortColumn == null || !widget.isSortable) return widget.rows;
    final col = widget.columns.firstWhere((c) => c.key == _sortColumn);
    final sorted = List<Map<String, dynamic>>.from(widget.rows);
    sorted.sort((a, b) {
      final aVal = (col.sortValue != null
              ? col.sortValue!(a[_sortColumn])
              : a[_sortColumn]?.toString()) ??
          '';
      final bVal = (col.sortValue != null
              ? col.sortValue!(b[_sortColumn])
              : b[_sortColumn]?.toString()) ??
          '';
      return _sortAscending
          ? Comparable.compare(aVal, bVal)
          : Comparable.compare(bVal, aVal);
    });
    return sorted;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isLoading) {
      return const Center(child: GulaLoading(type: GulaLoadingType.spinner));
    }

    if (widget.rows.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.inbox_outlined, size: 48, color: AppColors.neutral400),
            const SizedBox(height: 16),
            Text(
              widget.emptyMessage ?? 'No data available',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 16),
            ),
          ],
        ),
      );
    }

    final sortedRows = _sortedRows;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: DataTable(
              sortColumnIndex: widget.columns
                  .indexWhere((c) => c.key == _sortColumn),
              sortAscending: _sortAscending,
              columnSpacing: 24,
              headingRowHeight: 48,
              dataRowHeight: widget.rowHeight ?? AppDimensions.tableRowHeight,
              headingRowColor: WidgetStateProperty.all(AppColors.neutral50),
              horizontalMargin: 16,
              columns: _buildColumns(),
              rows: _buildRows(sortedRows),
            ),
          ),
        ),
        if (widget.totalPages != null && widget.totalPages! > 1)
          _buildPagination(),
      ],
    );
  }

  List<DataColumn> _buildColumns() {
    return widget.columns.map((col) {
      final isSorted = col.key == _sortColumn;
      return DataColumn(
        label: Text(
          col.label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
        numeric: col.textAlign == TextAlign.right,
        onSort: col.sortable
            ? (_, ascending) {
                setState(() {
                  if (_sortColumn == col.key) {
                    _sortAscending = !_sortAscending;
                  } else {
                    _sortColumn = col.key;
                    _sortAscending = ascending;
                  }
                });
              }
            : null,
      );
    }).toList();
  }

  List<DataRow> _buildRows(List<Map<String, dynamic>> rows) {
    return rows.asMap().entries.map((entry) {
      final index = entry.key;
      final row = entry.value;
      final key = row[widget.keyField!]?.toString() ?? index.toString();
      final isSelected = _selectedKeys.contains(key);

      return DataRow(
        key: ValueKey(key),
        selected: isSelected,
        onSelectChanged: widget.isSelectable
            ? (selected) {
                setState(() {
                  if (selected == true) {
                    _selectedKeys.add(key);
                  } else {
                    _selectedKeys.remove(key);
                  }
                  widget.onSelectionChanged?.call(Set.from(_selectedKeys));
                });
              }
            : null,
        cells: widget.columns.map((col) {
          final value = row[col.key];
          Widget cellWidget;
          if (col.cellBuilder != null) {
            cellWidget = col.cellBuilder!(value, row);
          } else {
            cellWidget = Text(
              value?.toString() ?? '',
              style: const TextStyle(fontSize: 13),
              textAlign: col.textAlign,
            );
          }
          return DataCell(cellWidget);
        }).toList(),
      );
    }).toList();
  }

  Widget _buildPagination() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.divider)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Text(
            '${widget.page} of ${widget.totalPages}',
            style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
          ),
          const SizedBox(width: 16),
          IconButton(
            icon: const Icon(Icons.chevron_left, size: 20),
            onPressed: widget.page != null && widget.page! > 1
                ? () => widget.onPageChanged?.call(widget.page! - 1)
                : null,
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right, size: 20),
            onPressed: widget.page != null && widget.page! < widget.totalPages!
                ? () => widget.onPageChanged?.call(widget.page! + 1)
                : null,
          ),
        ],
      ),
    );
  }
}
