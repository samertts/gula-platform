import 'package:flutter_test/flutter_test.dart';

import '../../lib/core/api/api_exceptions.dart';

void main() {
  test('maps a 404 API response to NotFoundException', () {
    final exception = parseApiError(
      <String, dynamic>{'detail': 'Not found'},
      404,
    );

    expect(exception, isA<NotFoundException>());
    expect(exception.message, 'Not found');
  });
}
