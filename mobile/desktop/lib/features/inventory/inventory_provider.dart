import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class InventoryProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _items = [];
  bool _isLoading = false;

  List<Map<String, dynamic>> get items => _items;
  bool get isLoading => _isLoading;

  Future<void> loadItems() async {
    _isLoading = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 300));
    _items = List.generate(
      15,
      (i) => {
        'id': '${i + 1}',
        'name': [
          'CBC Reagent',
          'LFT Reagent',
          'Glucose Reagent',
          'EDTA Tubes',
          'Plain Tubes',
          'Lancets',
          'Gloves',
          'Masks',
        ][i % 8],
        'category': [
          'Reagent',
          'Reagent',
          'Reagent',
          'Consumable',
          'Consumable',
          'Consumable',
          'Safety',
          'Safety',
        ][i % 8],
        'quantity': [50, 30, 100, 200, 150, 500, 1000, 800][i % 8],
        'minQuantity': [20, 20, 30, 100, 100, 200, 500, 500][i % 8],
        'unit': [
          'tests',
          'tests',
          'tests',
          'pcs',
          'pcs',
          'pcs',
          'pcs',
          'pcs',
        ][i % 8],
        'expiryDate': DateTime.now()
            .add(Duration(days: 30 * (i + 1)))
            .toIso8601String(),
      },
    );
    _isLoading = false;
    notifyListeners();
  }
}

final inventoryProvider = ChangeNotifierProvider<InventoryProvider>((ref) {
  return InventoryProvider();
});
