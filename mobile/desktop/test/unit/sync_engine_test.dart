import 'package:flutter_test/flutter_test.dart';

import '../../lib/core/offline/sync_engine.dart';

void main() {
  group('SyncStatus', () {
    test('exposes the complete synchronization lifecycle', () {
      expect(
        SyncStatus.values,
        containsAll(<SyncStatus>[
          SyncStatus.idle,
          SyncStatus.syncing,
          SyncStatus.pending,
          SyncStatus.error,
          SyncStatus.offline,
        ]),
      );
    });
  });
}
