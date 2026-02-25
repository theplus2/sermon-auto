---
description: 변경된 파일을 Git add, commit, push하여 GitHub에 자동으로 업로드한다
---

// turbo-all

1. 현재 변경된 파일 목록을 확인한다:
```
git -C "c:\Users\thepl\Desktop\Coding\sermon-auto" status
```

2. 변경된 파일을 전체 스테이징한다:
```
git -C "c:\Users\thepl\Desktop\Coding\sermon-auto" add .
```

3. 변경 내용을 요약하여 한국어로 커밋 메시지를 작성하고 커밋한다.
커밋 메시지는 사용자가 이번에 수정한 내용을 기반으로 의미있게 작성한다 (예: `refactor: ...`, `feat: ...`, `fix: ...` 등):
```
git -C "c:\Users\thepl\Desktop\Coding\sermon-auto" commit -m "[적절한 커밋 메시지]"
```

4. GitHub(origin/main)으로 푸시한다:
```
git -C "c:\Users\thepl\Desktop\Coding\sermon-auto" push
```

5. 결과를 사용자에게 보고한다. 커밋 해시, 변경된 파일 개수, GitHub 주소를 포함한다.
