import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/utils/constants.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class GlobalSearchPage extends StatefulWidget {
  const GlobalSearchPage({super.key});

  @override
  State<GlobalSearchPage> createState() => _GlobalSearchPageState();
}

class _GlobalSearchPageState extends State<GlobalSearchPage> {
  final _searchController = TextEditingController();
  String _query = '';

  final _results = <Map<String, dynamic>>[];

  void _search(String query) {
    setState(() => _query = query);
    if (query.length < 2) {
      setState(() => _results.clear());
      return;
    }

    _results.clear();
    _results.addAll(List.generate(5, (i) => {
      'type': ['patient', 'order', 'sample', 'result', 'patient'][i],
      'id': '${i + 1}',
      'title': ['Ahmed Ali', '#ORD-2025-0891', 'BL20250321-001', 'Hemoglobin', 'Sara Mohammed'][i],
      'subtitle': ['National ID: 10000000000001', 'CBC, LFT • Pending', 'Blood • Processing', '14.2 g/dL • Normal', 'Phone: 07701234567'][i],
    }));
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
              const SizedBox(width: 8),
              Expanded(
                child: GulaSearchBar(
                  hint: 'Search patients, orders, samples, results...',
                  controller: _searchController,
                  onChanged: _search,
                  autoFocus: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (_query.isNotEmpty && _results.isNotEmpty) ...[
            Text('${_results.length} results for "$_query"',
                style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: _results.length,
                itemBuilder: (context, index) {
                  final r = _results[index];
                  IconData icon;
                  Color iconColor;
                  String route;
                  switch (r['type']) {
                    case 'patient':
                      icon = Icons.person; iconColor = AppColors.primary500; route = '/patients/${r['id']}';
                    case 'order':
                      icon = Icons.assignment; iconColor = AppColors.info500; route = '/orders/${r['id']}';
                    case 'sample':
                      icon = Icons.science; iconColor = AppColors.accent500; route = '/samples/${r['id']}';
                    case 'result':
                      icon = Icons.description; iconColor = AppColors.success500; route = '/results/${r['id']}';
                    default:
                      icon = Icons.search; iconColor = AppColors.neutral500; route = '/';
                  }
                  return GulaCard(
                    onTap: () => context.push(route),
                    child: ListTile(
                      leading: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(color: iconColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                        child: Icon(icon, color: iconColor, size: 20),
                      ),
                      title: Text(r['title'], style: const TextStyle(fontWeight: FontWeight.w500)),
                      subtitle: Text(r['subtitle'], style: const TextStyle(fontSize: 12)),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          GulaBadge(label: r['type'], status: GulaBadgeStatus.neutral, showDot: false),
                          const SizedBox(width: 8),
                          const Icon(Icons.chevron_right, color: AppColors.neutral400),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ] else if (_query.isNotEmpty && _results.isEmpty) ...[
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.search_off, size: 64, color: AppColors.neutral300),
                    const SizedBox(height: 16),
                    Text('No results found for "$_query"',
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                  ],
                ),
              ),
            ),
          ] else ...[
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.search, size: 64, color: AppColors.neutral300),
                    const SizedBox(height: 16),
                    const Text('Search across patients, orders, samples, and results',
                        style: TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
