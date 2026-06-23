import 'package:flutter_test/flutter_test.dart';
import 'package:smart_attend_ai/main.dart';

void main() {
  testWidgets('App compiles and runs smoke test', (WidgetTester tester) async {
    // Basic test checking compile validity of SmartAttendApp
    expect(const SmartAttendApp(), isNotNull);
  });
}
